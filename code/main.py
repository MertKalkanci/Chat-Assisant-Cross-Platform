from copy import copy, deepcopy
from pprint import pprint
from re import T
import llama
import audio_manager
from file_operations import read_config, read_base_prompt
import flet as ft
import datetime
import asyncio
from plyer import notification

base_prompt = read_base_prompt()


class ChatterPage(ft.UserControl):
    old_prompts = ""
    commandList = []
    chat_index = 1
    current_chat_index = 1
    chat_history_element = {}
    prompt_history = {}
    
    def build(self):
        self.recorder = None
        self.messages = ft.Column(alignment=ft.CrossAxisAlignment.START)
        self.input = ft.TextField(hint_text="Type your message here", expand=True)
        self.record_button = ft.FloatingActionButton(icon=ft.icons.MIC, on_click=self.record_audio)
        self.send_button = ft.FloatingActionButton(icon=ft.icons.SEND, on_click=self.send_message)
        
        self.history_buttons = ft.Column([
            ft.Row([
                ft.FilledButton(text=f"Chat {self.chat_index}",on_click=self.load_chat),
                ft.FilledButton(text=f"Delete Chat {self.chat_index}",on_click=self.delete_chat)
                ])
        ])
        
        self.add_chat_button = ft.FilledButton(text=f"Create Chat",on_click=self.create_chat)

        view = ft.Row(
                [
                    ft.Column(
                    [
                        ft.Text("Chat List"),
                        self.history_buttons,  
                        self.add_chat_button,
                    ]),
                    ft.Column(
                    [
                        ft.Text("Chat"),
                        ft.Row([
                            self.input,
                            self.send_button,
                            self.record_button,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START),
                        self.messages,
                
                    ],    
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True),
                ]
            )
        
        
        return view
    
    def send_message(self, e=None, message=None):
        if message is None:
            message = self.input.value

        messageToSend = "USER:\n" + message

        if self.messages.controls is None:
            self.messages.controls = []

        self.messages.controls.append(self.message(message=message, is_user=True))
        self.messages.update()
        self.page.update()

        response = llama.generate_response((base_prompt + self.old_prompts + messageToSend + "BOT:"))
        self.old_prompts += messageToSend + "\nBOT:" + response + "\n"
        pprint(self.old_prompts)

        self.messages.controls.append(self.message(message=response, is_user=False))
        self.messages.update()
        self.page.update()
        
        notification.notify(
            title = 'Chat Completion Finished',
            message = 'Go to web browser and look for response generated by AI',
        timeout = 10
        )
        
    def create_chat(self, e=None):
        self.chat_index += 1
        
        self.save_chat(self.current_chat_index)
        
        self.messages.controls.clear()
        self.current_chat_index = self.chat_index
        self.history_buttons.controls.append(
            ft.Row([
                ft.FilledButton(text=f"Chat {self.chat_index}",on_click=self.load_chat),
                ft.FilledButton(text=f"Delete Chat {self.chat_index}",on_click=self.delete_chat)
                ])
            )
        
        if self.messages.controls is None:
            self.messages.controls = []  
        
        self.old_prompts = ""

        self.history_buttons.update()
        self.messages.update()
        self.page.update()
        
    def save_chat(self, current_chat_index):
        texts = []

        for element in self.messages.controls:
            bg = element.bgcolor
            texts.append(ft.Container(
                content=ft.Text(element.content.value,color=element.content.color),
                border_radius=10,
                bgcolor=bg,
                alignment=ft.alignment.top_left,
            ))

        self.chat_history_element[f"Chat {current_chat_index}"] = texts
        self.prompt_history[f"Chat {current_chat_index}"] = self.old_prompts

    def load_chat(self, e=None):
        self.save_chat(self.current_chat_index)
        
        text = "1"
        if e is not None:
            print(f"loading chat {e.control.text}")
            text = e.control.text
        else:
            print(f"loading chat 1")
        
        self.current_chat_index = int(''.join(x for x in str(text) if x.isdigit()))
        
        self.messages.controls.clear()
        
        if f"Chat {self.current_chat_index}" in self.chat_history_element:
            self.messages.controls = self.chat_history_element[f"Chat {self.current_chat_index}"]
            self.old_prompts = self.prompt_history[f"Chat {self.current_chat_index}"]
        
        self.messages.update()
        self.page.update()
        
    def delete_chat(self,e):
        #Most complicated part of the whole UI, It would be better simplified and changed
        print(f"deleting chat {e.control.text}")
        
        index_to_delete = int(''.join(x for x in str(e.control.text) if x.isdigit()))
        
        if self.current_chat_index == index_to_delete:
            print(f"not deleting chat {e.control.text}, page is still active")
            
            notification.notify(
            title = 'Cannot Delete Chat !',
            message = 'Go to another chat page and try again !',
            timeout = 10
            )
            return
        
        if f"Chat {self.current_chat_index}" in self.chat_history_element:
            self.chat_history_element.__delitem__(f"Chat {index_to_delete}")
            self.prompt_history.__delitem__(f"Chat {index_to_delete}")
        
        if len(self.history_buttons.controls) != (index_to_delete):
            for i in range(index_to_delete - 1, len(self.history_buttons.controls)):
                #move chat history
                if f"Chat {i + 1}" in self.chat_history_element:
                    self.chat_history_element[f"Chat {i}"] = deepcopy(self.chat_history_element[f"Chat {i + 1}"])
                    self.chat_history_element.__delitem__(f"Chat {i + 1}")
                    
                if f"Chat {i + 1}" in self.prompt_history:
                    self.prompt_history[f"Chat {i}"] = deepcopy(self.prompt_history[f"Chat {i + 1}"])
                    self.prompt_history.__delitem__(f"Chat {i + 1}")
                
                buttons = self.history_buttons.controls[i].controls # update buttons
                for button in buttons:
                    button.text = ''.join(x for x in str(button.text) if not x.isdigit()).join(f" {i}")
                    
                    
                self.history_buttons.controls[i].controls[0].update() # update visuals
                self.history_buttons.controls[i].controls[1].update()
                self.history_buttons.controls[i].update()
                self.history_buttons.update()
        
        self.history_buttons.controls.pop(index_to_delete - 1) #remove buttons
        self.chat_index -= 1
        
        self.history_buttons.update() #update visuals again
        
        self.load_chat() #load default chat
            
    
    def record_audio(self, e=None):
        if self.recorder is None:
            self.recorder = audio_manager.AudioRecording()
        self.recorder.recording()


        if self.recorder.record.is_set():
            self.record_button.icon = ft.icons.STOP
        else:
            print("stopped")
            self.record_button.icon = ft.icons.MIC
            self.record_button.update()
            self.page.update()

            self.send_message(message=self.recorder.analyze_audio())

        self.record_button.update()
        self.page.update()

    def message(self, message, is_user=True):
        if is_user:
            return ft.Container(
                content=ft.Text(message),
                border_radius=10,
                bgcolor="#3F3F3F",
                alignment=ft.alignment.top_left,

            )
        else:
            return ft.Container(
                        content=ft.Text(message, color="#000000"),
                        border_radius=10,
                        bgcolor="#F0F0F0",
                        alignment=ft.alignment.top_left,
                    )
    
def main(page: ft.Page):
    page.title = "Chat"
    page.theme_mode = ft.ThemeMode.DARK

    messaging = ChatterPage()

    page.add(messaging)
    page.update()



if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER,port = 5000)

