

from gui.Core.main import Core
from gui.Interface.main import Interface
from gui.Core.event import Event


class LiveEventController:

    def __init__(self, Core: Core, Interface: Interface):
        self.obj_Core = Core
        self.obj_event= Event(self.obj_Core.dict_db_details,self.obj_Core.dict_user_data)
        self.obj_Interface = Interface
        self.obj_LiveEventInterface = self.obj_Interface.dict_frames["live_feed"]
        self.update_entry_exit()
        self.check_notification()



    def update_entry_exit(self):
        pass
            # """Update entry and exit count every 5 seconds"""
            # entry_count, exit_count=self.obj_event.today_entry_exit_count()
            # self.obj_LiveEventInterface.entry_count.configure(text=str(entry_count))
            # self.obj_LiveEventInterface.exit_count.configure(text=str(exit_count))
            # print("entry count is ",entry_count)

            #self.obj_LiveEventInterface.entry_count.after(3000, self.update_entry_exit)

    def check_notification(self):
         pass
        # if self.obj_LiveEventInterface.restricted_vehicle_caught_signal:
        #     self.obj_Interface.dict_frames['home'].dot_label.configure(text="●")

        #     self.obj_LiveEventInterface.restricted_vehicle_caught_signal = False

        # # Schedule the function to run again after 1000ms (1 second)
        # self.obj_LiveEventInterface.after(3000, self.check_notification)


