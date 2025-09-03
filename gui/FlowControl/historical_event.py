from functools import partial

from gui.Core.main import Core
from gui.Interface.main import Interface
import datetime
from gui.Core.event import Event


class HistoricalEventController:
    # def __init__(self, Core: Core, Interface: Interface):
    #     self.obj_Core = Core
    #     self.obj_event= Event(self.obj_Core.dict_db_details,self.obj_Core.dict_user_data)
    #     self.obj_Interface = Interface
    #     self.obj_LiveEventInterface = self.obj_Interface.dict_frames["live_feed"]

    def __init__(self, Core: Core, Interface: Interface):
       
        self.obj_core = Core
        self.obj_Core = Core
        self.obj_event= Event(self.obj_Core.dict_db_details,self.obj_Core.dict_user_data)
        self.obj_Interface = Interface
        self.obj_HomeInterface = self.obj_Interface.dict_frames["home"]
        self.obj_event= Event(self.obj_Core.dict_db_details,self.obj_Core.dict_user_data)
        self.obj_HistoricalEventInterface = self.obj_Interface.dict_frames["historical_event"]
        self.count_entry_exit_balance()
        self.prev_id = ""
        self.obj_HomeInterface.button_historical_event.bind("<Button-1>", self.count_entry_exit_balance)
        self.bind_label_image()
        self.bind_buttons()

    def bind_label_image(self):
        pass
        # if self.obj_HistoricalEventInterface.current_Track_Id != self.prev_id:
        #     self.obj_Interface.dict_frames["notification"].selected_vehicle = self.obj_HistoricalEventInterface.current_Track_Id
        #     self.obj_HistoricalEventInterface.current_Track_Id=""
        # self.obj_HistoricalEventInterface.after(100, self.bind_label_image)

    def bind_buttons(self):
        pass
     
        # self.obj_HistoricalEventInterface.button_filter.configure(command=self.filter_popup)
        # self.obj_HistoricalEventInterface.button_select_sdate.configure(command=self.popup_sdate_dropdown)
        # self.obj_HistoricalEventInterface.button_select_edate.configure(command=self.popup_edate_dropdown)
        # self.obj_HistoricalEventInterface.button_select_vehicle.configure(command=self.popup_vehicle_dropdown)
        # self.obj_HistoricalEventInterface.button_cancel.configure(command=self.onclick_cancel)
        # self.obj_HistoricalEventInterface.button_ok.configure(command=self.onclick_ok)
        # self.obj_HistoricalEventInterface.button_next.configure(command=self.onclick_next)
        # self.obj_HistoricalEventInterface.button_previous.configure(command=self.onclick_previous)
        # self.obj_HistoricalEventInterface.on_form_ready = self.bind_add_popup_buttons


    def on_window_restored(self):
       
        try:
            self.obj_HomeInterface = self.obj_Interface.dict_frames["home"]

            if 'historical_event' in self.obj_Interface.dict_frames and hasattr(
                    self.obj_Interface.dict_frames['historical_event'], 'ack_window'):
                self.obj_Interface.obj_RootInterface.deiconify()
        except Exception as e:
            print(e)

    def bind_add_popup_buttons(self):
       
        self.obj_HistoricalEventInterface.ack_window.bind("<Map>", lambda event: self.on_window_restored())

        try:
            if (hasattr(self.obj_HistoricalEventInterface, 'add_vehicle_button') and
                    self.obj_HistoricalEventInterface.add_vehicle_button is not None):
                # Unbind any existing command first
                self.obj_HistoricalEventInterface.add_vehicle_button.configure(command=None)
                # Rebind the command
                self.obj_HistoricalEventInterface.add_vehicle_button.configure(command=self.onclick_ack_add_vehicle)

        except Exception as e:
           pass

    def onclick_ack_add_vehicle(self):
        pass
        # try:
        #     # Add the vehicle
        #     self.obj_Interface.dict_frames["vehicle_list"].add_Vechile(
        #         num=self.obj_HistoricalEventInterface.current_vehicle_number
        #     )

        #     # Reset the button state
        #     self.bind_add_popup_buttons()

        #     # Optional: Add confirmation message
        #     print(f"Vehicle {self.obj_HistoricalEventInterface.current_vehicle_number} added successfully")

        # except Exception as e:
        #     print(f"Error adding vehicle: {e}")
    def filter_popup(self):
        pass
        # self.obj_HistoricalEventInterface.toggle_filter_popup()

    def popup_sdate_dropdown(self):
        pass
        # if (self.obj_HistoricalEventInterface.bool_edate_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_edate_dropdown_opened = False
        # elif (self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened = False

        # if (self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened = False
        # else:
        #     self.obj_HistoricalEventInterface.open_calendar(
        #         entry_destination=self.obj_HistoricalEventInterface.entry_selected_sdate,
        #         i_row=2,
        #         i_rowspan=4)
        #     self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened = True

    def popup_edate_dropdown(self):
        pass
        # if (self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened = False
        # elif (self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None, )
        #     self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened = False

        # if (self.obj_HistoricalEventInterface.bool_edate_dropdown_opened is True):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_edate_dropdown_opened = False
        # else:
        #     self.obj_HistoricalEventInterface.open_calendar(
        #         entry_destination=self.obj_HistoricalEventInterface.entry_selected_edate,
        #         i_row=4,
        #         i_rowspan=3)
        #     self.obj_HistoricalEventInterface.bool_edate_dropdown_opened = True

    def popup_vehicle_dropdown(self):
        pass
        # if (self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_sdate_dropdown_opened = False
        # elif (self.obj_HistoricalEventInterface.bool_edate_dropdown_opened):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_edate_dropdown_opened = False

        # if (self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened is True):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened = False
        # else:
        #     list_vehicle = self.obj_core.obj_event.get_distinct_vehicles()
        #     self.obj_HistoricalEventInterface.popup_dropdown(
        #         list_vehicle,
        #         entry_destination=self.obj_HistoricalEventInterface.entry_selected_vehicle,
        #         i_row=6,
        #         i_rowspan=3)
        #     self.obj_HistoricalEventInterface.bool_vehicle_dropdown_opened = True

    def onclick_ok(self):
       
        # str_start_date = self.obj_HistoricalEventInterface.entry_selected_sdate.get()
        # str_end_date = self.obj_HistoricalEventInterface.entry_selected_edate.get()
        # str_start_hour = self.obj_HistoricalEventInterface.spinbox_shour.get()
        # str_end_hour = self.obj_HistoricalEventInterface.spinbox_ehour.get()
        # str_start_minute = self.obj_HistoricalEventInterface.spinbox_sminute.get()
        # str_end_minute = self.obj_HistoricalEventInterface.spinbox_eminute.get()
        # str_vehicle_number = self.obj_HistoricalEventInterface.entry_selected_vehicle.get()

        self.obj_HistoricalEventInterface.reset_interface()

        # dict_response = self.obj_core.obj_event.validate_filter_criteria(str_start_date, str_end_date,
        #                                                                  str_start_hour, str_end_hour,
        #                                                                  str_start_minute, str_end_minute,
        #                                                                  str_vehicle_number)
        # print(f"\n{dict_response["dict_filter_criteria"]}\n")
        # self.count_entry_exit_balance(
        #     data=[str_start_date, str_start_hour, str_start_minute, str_end_date, str_end_hour, str_end_minute,
        #           str_vehicle_number])

        # if (dict_response["str_error_msg_heading"] == "" and dict_response["str_error_msg"] == ""):
        #     self.obj_HistoricalEventInterface.dict_filter_criteria = dict_response["dict_filter_criteria"]
        #     self.obj_HistoricalEventInterface.i_total_data = self.obj_core.obj_event.get_data_count(
        #         self.obj_HistoricalEventInterface.dict_filter_criteria)
        #     list_historical_events, self.obj_Interface.dict_frames[
        #         "historical_event"].event_starting_date = self.obj_core.obj_event.fetch_events(
        #         self.obj_HistoricalEventInterface.i_end_index, self.obj_HistoricalEventInterface.dict_filter_criteria)
        #     i_total_data_fetched = len(list_historical_events)
        #     if (i_total_data_fetched > 0):
        #         self.obj_HistoricalEventInterface.i_start_index = 1
        #         self.obj_HistoricalEventInterface.i_end_index += i_total_data_fetched
        #     self.obj_HistoricalEventInterface.update_table(list_historical_events)
        # else:
        #     self.obj_Interface.on_error(
        #         "home",
        #         dict_response["str_error_msg_heading"],
        #         dict_response["str_error_msg"]
        #     )

    def onclick_cancel(self):
        pass
        # self.obj_HistoricalEventInterface.reset_filter_form()
        # if (self.obj_HistoricalEventInterface.bool_filter_popup is True):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.reset_filter_form()
        #     self.obj_HistoricalEventInterface.toggle_filter_popup()

    def onclick_next(self):
        pass
        # if (self.obj_HistoricalEventInterface.bool_filter_popup is True):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.reset_filter_form()
        #     self.obj_HistoricalEventInterface.toggle_filter_popup()

        # list_historical_events, self.obj_Interface.dict_frames[
        #     "historical_event"].event_starting_date = self.obj_core.obj_event.fetch_events(
        #     self.obj_HistoricalEventInterface.i_end_index, self.obj_HistoricalEventInterface.dict_filter_criteria)
        # i_data_count = len(list_historical_events)
        # if (i_data_count > 0):
        #     self.obj_HistoricalEventInterface.i_start_index = self.obj_HistoricalEventInterface.i_end_index + 1
        #     self.obj_HistoricalEventInterface.i_end_index = self.obj_HistoricalEventInterface.i_end_index + i_data_count

        #     self.obj_HistoricalEventInterface.update_table(list_historical_events)

    def onclick_previous(self):
        pass
     
        # if (self.obj_HistoricalEventInterface.bool_filter_popup is True):
        #     self.obj_HistoricalEventInterface.close_dropdown(None)
        #     self.obj_HistoricalEventInterface.reset_filter_form()
        #     self.obj_HistoricalEventInterface.toggle_filter_popup()

        # i_start_index = self.obj_HistoricalEventInterface.i_start_index - 10
        # if (i_start_index < 0):
        #     i_start_index = 1
        # list_historical_events, self.obj_Interface.dict_frames[
        #     "historical_event"].event_starting_date = self.obj_core.obj_event.fetch_events(i_start_index,
        #                                                                                    self.obj_HistoricalEventInterface.dict_filter_criteria)
        # i_data_count = len(list_historical_events)
        # if (i_data_count > 0):
        #     self.obj_HistoricalEventInterface.i_start_index = i_start_index
        #     self.obj_HistoricalEventInterface.i_end_index = (i_start_index + i_data_count) - 1

        #     self.obj_HistoricalEventInterface.update_table(list_historical_events)



    def count_entry_exit_balance(self,event=None, data=[]):
        pass

        # if data ==[]:
        #     str_start_date = self.obj_HistoricalEventInterface.entry_selected_sdate.get()
        #     str_end_date = self.obj_HistoricalEventInterface.entry_selected_edate.get()
        #     str_start_hour = self.obj_HistoricalEventInterface.spinbox_shour.get()
        #     str_end_hour = self.obj_HistoricalEventInterface.spinbox_ehour.get()
        #     str_start_minute = self.obj_HistoricalEventInterface.spinbox_sminute.get()
        #     str_end_minute = self.obj_HistoricalEventInterface.spinbox_eminute.get()
        #     str_vehicle_number = self.obj_HistoricalEventInterface.entry_selected_vehicle.get()
        # else:
        #     str_start_date = data[0]
        #     str_end_date = data[3]
        #     str_start_hour = data[1]
        #     str_end_hour = data[4]
        #     str_start_minute = data[2]
        #     str_end_minute = data[5]
        #     str_vehicle_number = data[6]

        # try:
        #     start_date_obj = datetime.datetime.strptime(str_start_date, "%d-%m-%Y")
        #     end_date_obj =datetime.datetime.strptime(str_end_date, "%d-%m-%Y")

        #     # Formatting the dates to yyyy-mm-dd format
        #     str_start_date = start_date_obj.strftime("%Y-%m-%d")
        #     str_end_date = end_date_obj.strftime("%Y-%m-%d")

        #     # Adding the Time back to the formatted dates
        #     str_start_date = f"{str_start_date} {str_start_hour}:{str_start_minute}:00"
        #     str_end_date = f"{str_end_date} {str_end_hour}:{str_end_minute}:59"


        #     if str_vehicle_number == "Select Vehicle" or str_vehicle_number == "All":
        #         str_vehicle_number='%'



        #     print("Data from filter:", str_start_date, "\n", str_end_date)
        # except ValueError as e:
        #     print("Error:", e)

        # dict_filter_criteria = {
        #     "str_start_Timeperiod": str_start_date,
        #     "str_end_Timeperiod": str_end_date,
        #     "str_vehicle_number": str_vehicle_number

        # }
        # print( " data format " , dict_filter_criteria)

