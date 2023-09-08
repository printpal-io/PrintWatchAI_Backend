import datetime
import aiohttp
from uuid import uuid4

class PrintWatchClient():
    '''
    The object that handles API communications with the PrintWatch cloud server
    '''
    def __init__(
            self,
            settings : dict,
            stream=None,
            ssl : bool = True
        ):
        self.route = 'https://ai.printpal.io' if ssl else 'http://ai.printpal.io'
        self.settings = settings
        self.ticket_id = ''

    def create_ticket(self):
        self.ticket_id = uuid4().hex

    def clear_ticket(self):
        self.ticket_id = ''

    def _create_payload(
            self,
            encoded_image,
            scores : list = [],
            print_stats : dict = {},
            notify : bool = False,
            notification_level : str = 'warning'
        ):
        if notify:
            payload = {
                "api_key" : self.settings.get("api_key"),
                "printer_id" : self.settings.get("printer_id"),
                "email_addr" : self.settings.get("email_addr"),
                "printTime" : print_stats.get("printTime", 550),
                "printTimeLeft" : print_stats.get("printTimeLeft", 1),
                "progress" : print_stats.get("progress", 0),
                "job_name" : print_stats.get("job_name", "none"),
                "notification" : notification_level,
                "time" : datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            }
        else:
            if self.ticket_id == '':
                self.create_ticket()

            payload = {
                'api_key' : self.settings.get("api_key"),
                'printer_id' : self.settings.get("printer_id"),
                'ticket_id' : self.ticket_id,
                'version' : '1.2.11',
                'state' : 0,
                'conf' : int(self.settings.get("thresholds", {}).get("display", 0.6) * 100),
                'buffer_length' : self.settings.get("buffer_length"),
                'buffer_percent' : self.settings.get("buffer_percent"),
                'thresholds' : [self.settings.get("thresholds", {}).get("notification", 0.3), self.settings.get("thresholds", {}).get("action", 0.6)],
                'scores' : scores,
                'sma_spaghetti' : 0,
                'email_addr' : self.settings.get("email_addr"),
                'enable_feedback_images' : True
            }
            for key, ele in print_stats.items():
                payload[key] = ele
                
            payload['image_array'] = encoded_image

        return payload


    async def _send_async(
                self,
                endpoint,
                payload
            ):

            async with aiohttp.ClientSession() as session:
                async with session.post(
                                '{}/{}'.format(self.route, endpoint),
                                json = payload,
                                headers={'User-Agent': 'Mozilla/5.0'},
                                timeout=aiohttp.ClientTimeout(total=30.0)
                            ) as response:
                            r = await response.json()

            self.response = r
            return r
