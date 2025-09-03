import logging
from tkinter import StringVar


# from share_queue import all_camera_data, current_camera_details, update_camera_details, update_all_camera_list
from gui.Core.main import Core
from gui.Interface.main import Interface


class HomeController:
    _instance = None

    def __new__(cls, Core, Interface):
        pass
        if cls._instance is None:
            cls._instance = super(HomeController, cls).__new__(cls)
            cls._instance.init(Core, Interface)
        return cls._instance

    def init(self, Core, Interface):
     
        self.obj_Core = Core
        self.obj_Interface = Interface
        self.obj_HomeInterface = self.obj_Interface.dict_frames["home"]
        self.bind_buttons()
        self.bind_settings_buttons()
        # self.restore_all_Camera_Name()
        # self.set_Camera_Name()
        # self.obj_HomeInterface.bind("<Unmap>", lambda event: self.on_minimize(event))
        # self.obj_HomeInterface.bind("<Map>", lambda event: self.on_window_restored(event))



    def set_Camera_Name(self):
        pass
      
 
        # """
        # Set the camera name in the home interface based on available camera data.
        # Prioritize a camera named 'rtsp' if available; otherwise, use the first camera in the data.
        # """
        # try:

        #     count = self.obj_Core.obj_Camera.get_camera_count()
        #     camera_data = self.obj_Core.obj_Camera.fetch_all_Camera_data()
        #     for camera in camera_data:
        #         camera_info = {
        #             "Camera_Name": camera.get('Camera_Name', 'N/A'),
        #             "roi_start": camera.get('ROIStartPercentageHeight', '0'),
        #             'roi_end': camera.get('ROIEndPercentageHeight', '0'),
        #             "roi_start_width": camera.get('ROIStartPercentageWidth', '0'),
        #             'roi_end_width': camera.get('ROIEndPercentageWidth', '0'),
        #             "Status": camera.get('Camera_direction', 'N/A'),
        #             "rtsp_url": camera.get('URL', 'N/A')
        #         }

        #         # all_camera_data.append(camera_info)

        #     if count > 0 and camera_data:
        #         # Use the first camera from the list
        #         selected_Camera_Name = camera_data[0].get('Camera_Name', 'N/A')
        #         self.obj_HomeInterface.selected_camera = selected_Camera_Name
        #         # update_camera_details(camera_data[0].get('Camera_Name', ''), camera_data[0].get('URL', ''),
        #         #                       camera_data[0].get('ROIStartPercentageHeight', '15'),
        #         #                       camera_data[0].get('ROIEndPercentageHeight', '90'),
        #         #                       camera_data[0].get('ROIStartPercentageWidth', '15'),
        #         #                       camera_data[0].get('ROIEndPercentageWidth', '90'),
        #         #                       camera_data[0].get('Camera_direction', ''))
        #         # self.obj_HomeInterface.entry_selected_camera.configure(
        #         #     textvariable=StringVar(value=selected_Camera_Name)
        #         # )
        #     else:
        #         self.obj_HomeInterface.selected_camera = ''
        #         self.obj_HomeInterface.entry_selected_camera.configure(
        #             textvariable=StringVar(value='N/A')
        #         )

        # except Exception as e:
        #     print(e)

    def on_minimize(self, event=None):
        try:
            pass
            # Check if 'camera_manager' exists in the dictionary and has a 'popup' attribute
            # if 'camera_manager' in self.obj_Interface.dict_frames and hasattr(
            #         self.obj_Interface.dict_frames['camera_manager'], 'popup'):
            #     self.obj_Interface.dict_frames['camera_manager'].popup.iconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during minimize: {e}")
        # try:
        #     pass
           
            # if 'vehicle_list' in self.obj_Interface.dict_frames and hasattr(
            #         self.obj_Interface.dict_frames['vehicle_list'], 'popup'):
            #     self.obj_Interface.dict_frames['vehicle_list'].popup.iconify()

        except Exception as e:
            logging.error(f"An error occurred during minimize: {e}")

        # try:

        #     if  hasattr(self.obj_Interface.dict_frames['historical_event'], 'ack_window'):

        #         self.obj_Interface.dict_frames['historical_event'].ack_window.iconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during minimize: {e}")

        # try:
        #     pass

        #     # if hasattr(self.obj_Interface.dict_frames['notification'], 'ack_window'):

        #     #     self.obj_Interface.dict_frames['notification'].ack_window.iconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during minimize: {e}")
        


    def on_window_restored(self, event=None):
        pass
      
        # try:
        #     pass
            # Check if 'camera_manager' exists in the dictionary and has a 'popup' attribute
        #     if 'camera_manager' in self.obj_Interface.dict_frames and hasattr(
        #             self.obj_Interface.dict_frames['camera_manager'], 'popup'):
        #         self.obj_Interface.dict_frames['camera_manager'].popup.deiconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during restore: {e}")
        # try:
        #     # Check if 'vehicle_list' exists in the dictionary and has a 'popup' attribute
        #     if 'vehicle_list' in self.obj_Interface.dict_frames and hasattr(
        #             self.obj_Interface.dict_frames['vehicle_list'], 'popup'):
        #         self.obj_Interface.dict_frames['vehicle_list'].popup.deiconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during restore: {e}")

        # try:

        #     if  hasattr(self.obj_Interface.dict_frames['historical_event'], 'ack_window'):

        #         self.obj_Interface.dict_frames['historical_event'].ack_window.deiconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during minimize: {e}")

        # try:

        #     if hasattr(self.obj_Interface.dict_frames['notification'], 'ack_window'):

        #         self.obj_Interface.dict_frames['notification'].ack_window.deiconify()

        # except Exception as e:
        #     logging.error(f"An error occurred during minimize: {e}")


    def restore_all_Camera_Name(self):
        pass
        # all_camera = self.obj_Core.obj_Camera.fetch_all_Camera_data()
        # Camera_Names = [camera['Camera_name'] for camera in all_camera]
        # self.obj_HomeInterface.list_camera = Camera_Names

    def bind_buttons(self) -> None:
        # print("bins buttonn ))))))))))))))))))))))))))))))))))))")
     
        self.obj_HomeInterface.button_live_event.configure(
            command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_live_event))
        # self.obj_HomeInterface.button_add_vehicle.configure(
        #     command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_add_vehicle))
        # self.obj_HomeInterface.button_vehicle_list.configure(
        #     command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_vehicle_list))
        # self.obj_HomeInterface.button_delete_vehicle.configure(
        #     command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_delete_vehicle))
        self.obj_HomeInterface.button_historical_event.configure(
            command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_historical_event))
        # self.obj_HomeInterface.button_menu.configure(command=self.onclick_menu)
        # self.obj_HomeInterface.button_user.configure(command=self.onclick_user_button)
        # self.obj_HomeInterface.button_edit.configure(
        #     command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_edit))
        # self.obj_HomeInterface.button_create_user.configure(
        #     command=lambda: self.onclick_menu_buttons(self.obj_HomeInterface.button_create_user))
        # self.obj_HomeInterface.button_signout_1.configure(command=self.onclick_signout)
        # self.obj_HomeInterface.button_signout_2.configure(command=self.onclick_signout)
        # self.obj_HomeInterface.button_notification.configure(
        #     command=self.onclick_notification_button)
        # self.obj_HomeInterface.button_settings.configure(
        #     command=self.onclick_settings_button
        # )


    def onclick_camera_manager(self):
        print("camera          mangemnt paggggggg")
      
        # self.obj_HomeInterface.update_menu_buttons_state(self.obj_HomeInterface.button_camera_settings)
        self.obj_Interface.switch_frames('camera_manager')

    def onclick_audio_manager(self) -> None:
        pass
       
        # self.obj_Interface.dict_frames['camera_manager'].reset_interface()
        # self.obj_HomeInterface.update_menu_buttons_state(self.obj_HomeInterface.button_audio_settings)
        # self.obj_Interface.switch_frames('audio_manager')

    def bind_settings_buttons(self) -> None:
        pass
        
     
        # """Bind the settings submenu buttons after they are created"""
        # if hasattr(self.obj_HomeInterface, 'button_camera_settings'):
        #     self.obj_HomeInterface.button_camera_settings.configure(
        #         command=lambda: self.onclick_submenu_button("camera")
        #     )
        # if hasattr(self.obj_HomeInterface, 'btn_vehicle_manager'):
        #     self.obj_HomeInterface.btn_vehicle_manager.configure(
        #         command=lambda: self.onclick_submenu_button("vehicle_list")
        #     )
        # if hasattr(self.obj_HomeInterface, 'button_audio_settings'):
        #     self.obj_HomeInterface.button_audio_settings.configure(
        #         command=lambda: self.onclick_audio_manager()
        #     )

    def onclick_settings_button(self) -> None:
        pass
        # """Handle settings button click and bind submenu buttons"""
        # # Update the settings button state first
        self.obj_HomeInterface.update_menu_buttons_state(self.obj_HomeInterface.button_settings)
        # Then toggle the popup
        self.obj_HomeInterface.toggle_settings_popup()
        # Bind the submenu buttons
        self.bind_settings_buttons()

    def onclick_submenu_button(self, option: str) -> None:

        # self.obj_Interface.dict_frames["add_vehicle"].reset_interface()
        # self.obj_Interface.dict_frames["delete_vehicle"].reset_interface()
        # self.obj_Interface.dict_frames["vehicle_list"].reset_interface()
        # self.obj_Interface.dict_frames["historical_event"].reset_interface()
        # self.obj_Interface.dict_frames['camera_manager'].reset_interface()
        # self.obj_Interface.dict_frames['vehicle_list'].reset_checkbox()

        if option == "camera":
        
          
            # Update button state for camera manager
            # self.obj_HomeInterface.update_menu_buttons_state(self.obj_HomeInterface.button_camera_settings)
            # self.obj_Interface.dict_frames['camera_manager'].update_camera_data_list()
            # self.obj_Interface.dict_frames['camera_manager'].update_table(self.obj_Interface.dict_frames['camera_manager'].dummy_camera_details)
            # self.obj_HomeInterface.hide_frame_camera()
            self.obj_Interface.switch_frames('camera_manager')


        elif option == 'vehicle_list':
            pass
            # self.obj_Interface.dict_frames['camera_manager'].reset_interface()

            # self.obj_HomeInterface.hide_frame_camera()
            # self.obj_HomeInterface.update_menu_buttons_state(self.obj_HomeInterface.btn_vehicle_manager)
            # self.obj_Interface.switch_frames("vehicle_list")

        elif option == 'audio':
            pass
            # self.obj_Interface.dict_frames['camera_manager'].reset_interface()
            # # Update button state for audio manager
            # self.obj_HomeInterface.update_menu_buttons_state(self.obj_HomeInterface.button_audio_settings)
            # self.obj_HomeInterface.hide_frame_camera()
            # self.obj_Interface.switch_frames('audio_manager')

    def onclick_camera_button(self, frame_name: str, button) -> None:
        pass
        """Handle camera-related button clicks without destroying the camera menu"""
        # self.obj_HomeInterface.update_menu_buttons_state(button)  # Update the state of the clicked button
        # self.obj_Interface.switch_frames(frame_name)

    # def onclick_menu_buttons(self, button_menu) -> None:
       

    #    if (button_menu == self.obj_HomeInterface.button_historical_event):
    #         print(button_menu,"*************************************-----------------------------------")
    #         self.obj_Interface.switch_frames("historical_event")
    #         # Reset interfaces
    #         # self.obj_Interface.dict_frames["add_vehicle"].reset_interface()
    #         # self.obj_Interface.dict_frames["delete_vehicle"].reset_interface()

    #         self.obj_Interface.dict_frames["historical_event"].reset_interface()
    #         # self.obj_Interface.dict_frames['camera_manager'].reset_interface()
    #     if (button_menu == self.obj_HomeInterface.button_live_event):
    #             print("************************************** live feed*******************************")
    #             self.obj_Interface.switch_frames("live_feed")
    #             self.obj_Interface.dict_frames["live_feed"].reset_interface()
            
          
    #             # self.restore_all_Camera_Name()
                
    #             # self.obj_HomeInterface.show_frame_camera()

    #     if (button_menu == self.obj_HomeInterface.button_historical_event):
    #         print("************************************** historical_event feed*******************************")
            
    #         self.obj_Interface.switch_frames("historical_event")
    #         self.obj_Interface.dict_frames["historical_event"].reset_interface()
            
    #         list_historical_events, self.obj_Interface.dict_frames[
    #             "historical_event"].event_starting_date = self.obj_Core.obj_event.fetch_events(
    #             self.obj_Interface.dict_frames["historical_event"].i_end_index,
    #             self.obj_Interface.dict_frames["historical_event"].dict_filter_criteria)
    #         self.obj_Interface.dict_frames["historical_event"].i_total_data = self.obj_Core.obj_event.get_data_count(
    #             self.obj_Interface.dict_frames["historical_event"].dict_filter_criteria)
    #         i_total_data_fetched = len(list_historical_events)
    #         if (i_total_data_fetched > 0):
    #             self.obj_Interface.dict_frames["historical_event"].i_start_index = 1
    #             self.obj_Interface.dict_frames["historical_event"].i_end_index += i_total_data_fetched
    #         self.obj_Interface.dict_frames["historical_event"].update_table(list_historical_events)
    #         self.obj_Interface.switch_frames("historical_event")
    #     elif (button_menu == self.obj_HomeInterface.button_settings):
    #         self.obj_Interface.switch_frames("settings")

    def onclick_menu_buttons(self, button_menu) -> None:

        if button_menu == self.obj_HomeInterface.button_live_event:
            print("************************************** live feed*******************************")
            self.obj_Interface.switch_frames("live_feed")
            self.obj_Interface.dict_frames["live_feed"].reset_interface()

        elif button_menu == self.obj_HomeInterface.button_historical_event:
            print("************************************** historical_event feed*******************************")
            self.obj_Interface.switch_frames("historical_event")

            # Reset interface
            self.obj_Interface.dict_frames["historical_event"].reset_interface()

            # Fetch historical events
            list_historical_events, self.obj_Interface.dict_frames[
                "historical_event"].event_starting_date = self.obj_Core.obj_event.fetch_events(
                self.obj_Interface.dict_frames["historical_event"].i_end_index,
                self.obj_Interface.dict_frames["historical_event"].dict_filter_criteria)

            self.obj_Interface.dict_frames["historical_event"].i_total_data = self.obj_Core.obj_event.get_data_count(
                self.obj_Interface.dict_frames["historical_event"].dict_filter_criteria)

            i_total_data_fetched = len(list_historical_events)
            if i_total_data_fetched > 0:
                self.obj_Interface.dict_frames["historical_event"].i_start_index = 1
                self.obj_Interface.dict_frames["historical_event"].i_end_index += i_total_data_fetched

            self.obj_Interface.dict_frames["historical_event"].update_table(list_historical_events)

        elif button_menu == self.obj_HomeInterface.button_settings:
            self.obj_Interface.switch_frames("settings")





    

    def onclick_menu(self) -> None:
        self.obj_HomeInterface.toggle_menu_bar()

    def onclick_user_button(self) -> None:
        self.obj_HomeInterface.toggle_user_popup()

    def onclick_signout(self) -> None:
        if (self.obj_HomeInterface.bool_user_popup is True):
            self.obj_HomeInterface.toggle_user_popup()

        self.obj_Interface.dict_frames["home"].starting_home_screen()
        self.obj_Interface.switch_frames("signin")