from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .client import *
from .utils import LoopHandler, Scheduler, _async_heartbeat, RepRapAPI, test_url
from .interface import *
import asyncio
import ujson
import uvicorn
import os
from pydantic import BaseModel
from typing import Optional, Union
from threading import Thread
from contextlib import asynccontextmanager

origins = [
    "*",
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:8989",
]

class Settings(BaseModel):
    api_key : Optional[str] = None
    printer_id : Optional[str] = None
    duet_ip : Optional[str] = None
    backendAddr : Optional[str] = None
    camera_ip : Optional[str] = None
    email_addr : Optional[str] = None
    test_mode : Optional[bool] = None
    notification_threshold : Optional[float] = None
    action_threshold : Optional[float] = None
    display_threshold : Optional[float] = None
    buffer_length : Optional[int] = None
    buffer_percent : Optional[int] = None
    pause_action : Optional[bool] = None
    cancel_action : Optional[bool] = None
    notify_action : Optional[bool] = None
    extruder_off_action : Optional[bool] = None
    pause_gcode : Optional[str] = None


def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

class PrintFarmPro:
    '''
    This is the main object that controls all of the other objects and functions

    '''
    def __init__(
            self
        ):
        '''
        Load settings, create API endpoints, and begin the program.

        '''
        self.runner = None
        self.printwatch = None
        self.rep_rap_api = None
        self._load_settings()
        self.aio = get_or_create_eventloop()

        if self.settings.get("monitoring_on"):
            self._init_monitor()


        self.router = APIRouter()
        self.router.add_api_route('/machine/printwatch/set_settings', self._change_settings, methods=["POST"])
        self.router.add_api_route('/machine/printwatch/get_settings', self._get_settings, methods=["GET"])
        self.router.add_api_route('/machine/printwatch/monitor', self._get_monitor, methods=["GET"])
        self.router.add_api_route('/machine/printwatch/preview', self._get_preview, methods=["GET"])
        self.router.add_api_route('/machine/printwatch/monitor_init', self._add_monitor, methods=["GET"])
        self.router.add_api_route('/machine/printwatch/monitor_off', self._kill_monitor, methods=["GET"])
        self.router.add_api_route('/machine/printwatch/heartbeat', self._heartbeat, methods=["GET"])
        self.router.add_api_route('/machine/printwatch/test_url', self._test_url, methods=["GET"])
        self._init_api(self.aio)

        #self.aio = get_or_create_eventloop()


    def _init_api(self, loop):
        self.app = FastAPI()
        self.app.include_router(self.router)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        cfg = uvicorn.Config(self.app, loop=loop, host='0.0.0.0', port=8989)
        server = uvicorn.Server(cfg)
        loop.run_until_complete(server.serve())


    def _on_settings_change(self):
        if self.printwatch is None:
            self.printwatch = PrintWatchClient(settings=self.settings)
        settings_ = {
                    'detection_threshold' : int(self.settings.get("thresholds", {}).get("display", 0.6) * 100),
                    'buffer_length' : int(self.settings.get("buffer_length")),
                    'notification_threshold' : int(self.settings.get("thresholds", {}).get("notification", .30) * 100),
                    'action_threshold' : int(self.settings.get("thresholds", {}).get("action", .60) * 100),
                    'enable_notification' : self.settings.get("actions", {}).get("notify", False),
                    'email_address' : self.settings.get("email_addr"),
                    'pause_print' : self.settings.get("actions", {}).get("pause", False),
                    'cancel_print' : self.settings.get("actions", {}).get("cancel", False),
                    'extruder_heat_off' : self.settings.get("actions", {}).get("extruder_off", False),
                    'enable_feedback_images' : True
                }
        asyncio.ensure_future(_async_heartbeat(api_client=self.printwatch, settings=settings_))

        if self.settings.get("printer_id", "") == "" or (self.settings.get("duet_ip") != "" and '-' not in self.rep_rap_api.uniqueId):
            self.rep_rap_api._get_uid()
            self.settings["printer_id"] = self.rep_rap_api.uniqueId
        if self.runner is not None:
            self.runner._loop_handler.resize_buffers()
            self.runner._loop_handler.camera.ip = self.settings.get("camera_ip")

    def _save_settings(self):
        with open("settings.json", "w") as f:
            ujson.dump(self.settings, f, indent=4)

    def _load_settings(self):
        if not os.path.exists("settings.json"):
            self.settings = {
                "api_key" : "",
                "printer_id" : "",
                "duet_ip" : "",
                "camera_ip" : "",
                "email_addr" : "",
                "test_mode" : False,
                "monitoring_on" : False,
                "thresholds" : {
                    "notification" : 0.3,
                    "action" : 0.6,
                    "display" : 0.6
                },
                "buffer_length" : 16,
                "buffer_percent" : 60,
                "actions": {
                    "pause" : False,
                    "cancel" : False,
                    "notify" : False,
                    "extruder_off" : False,
                    "macro" : False
                },
                "current_sma" : 0.0,
                "require_sync" : 0, # Enum value, {0 : no sync required, 1 : backend has correct value, 2: frontend has correct}
                "pause_gcode" : ""
            }
            self.rep_rap_api = RepRapAPI(settings=self.settings)
            self._on_settings_change()
            self._save_settings()
        else:
            with open("settings.json", "r") as f:
                self.settings = ujson.load(f)
            self.rep_rap_api = RepRapAPI(settings=self.settings)
            self._on_settings_change()


    def _init_monitor(self, ticket_id : str = ''):
        if self.runner is not None:
            return False
        loop = LoopHandler(
                        settings=self.settings,
                        api_client=self.printwatch,
                        rep_rap_api=self.rep_rap_api,
                        camera=MJPEG(ip=self.settings.get("camera_ip"))
                    )
        self.runner = Scheduler(interval=10.0, loop_handler=loop)
        self.settings["monitoring_on"] = True
        self._save_settings()
        self._on_settings_change()
        return True

    def _kill_runner(self):
        self.runner.cancel()
        self.runner = None
        self.settings["monitoring_on"] = False
        self._save_settings()
        self._on_settings_change()

    async def _get_monitor(self):
        if self.runner is None:
            return {'status' : 8001, 'response' : 'No monitor active'}
        return {'status' : 8000,
                'items' :
                    {'status' :
                        {'scores' : self.runner._loop_handler._scores,
                        'levels' : self.runner._loop_handler._levels,
                        'buffer' : self.runner._loop_handler._buffer
                        }
                    }
                }

    async def _test_url(self):
        r_ = await test_url(self.settings.get("camera_ip"))
        return r_

    async def _get_preview(self):
        if self.runner is None:
            return {'status' : 8001, 'response' : 'No monitor active'}
        return {'status' : 8000,
                'items' :
                    {'status' :
                        {'preview' : self.runner._loop_handler.currentPreview
                        }
                    }
                }

    async def _heartbeat(self, api_key : Union[str, None] = None, test_mode : Union[bool, None] = None, enable_monitor : Union[bool, None] = None, duet_ip : Union[str, None] = None):
        unsynced_variables = {
            'duet_ip' : False,
            'api_key' : False,
            'test_mode' : False,
            'monitoring_on' : False
        }
        if self.settings.get("require_sync", 0) == 1:
            self.settings["require_sync"] = 0
            return {'status' : 8002, 'settings' : self.settings}
        if self.settings['duet_ip'] != duet_ip and duet_ip not in ['', None]:
            unsynced_variables['duet_ip'] = True
            self.settings['duet_ip'] = duet_ip
        if self.settings['api_key'] != api_key and api_key not in ['', None]:
            unsynced_variables['api_key'] = True
            self.settings['api_key'] = api_key
        if self.settings['monitoring_on'] != enable_monitor and enable_monitor is not None:
            unsynced_variables["monitoring_on"] = True
            self.settings['monitoring_on'] = enable_monitor
            if self.settings["monitoring_on"] is False:
                self._kill_runner()
        if self.settings['test_mode'] != test_mode and test_mode is not None:
            unsynced_variables["test_mode"] = True
            self.settings["test_mode"] = test_mode

        if self.settings['monitoring_on'] and self.runner is None:
            r_ = self._init_monitor()

        if any(unsynced_variables.values()):
            self._save_settings()
            self._on_settings_change()
            return {'status' : 8001, 'unsynced' : unsynced_variables}

        return {'status' : 8000}


    async def _change_settings(self, settings : Settings):
        for key, value in settings.__dict__.items():
            if value is not None:
                if key == 'notification_threshold':
                    if value not in [0.0, 0]:
                        self.settings['thresholds']['notification'] = value if value < 1.0 else value / 100.
                elif key == 'action_threshold':
                    if value not in [0.0, 0]:
                        self.settings['thresholds']['action'] = value if value < 1.0 else value / 100.
                elif key == 'notify_action':
                    self.settings['actions']['notify'] = value
                elif key == 'pause_action':
                    self.settings['actions']['pause'] = value
                elif key == 'duet_ip':
                    if value not in ['', None]:
                        self.settings[key] = value
                else:
                    self.settings[key] = value
        self._save_settings()
        self._on_settings_change()
        return {'status' : 8000}

    async def _get_settings(self):
        return {'status' : 8000, 'settings' : self.settings}


    async def _add_monitor(self):
        result = self._init_monitor()
        if result:
            return {'status' : 8000}
        return {'status' : 8001, 'response' : 'Monitor loop already exists'}

    async def _kill_monitor(self):
        try:
            self._kill_runner()
            return {'status' : 8000}
        except Exception as e:
            return {'status' : 8001, 'response' : str(e)}
