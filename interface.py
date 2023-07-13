from sqlalchemy import create_engine
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token, db_url_object
from core import VkTools
from data_store import add_user, check_user

engine = create_engine(db_url_object)

# отправка сообщений

class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0
          
      #функция отправки сообщений
      
    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       ) 

# диалог с ботом

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                
                if event.text.lower() == 'привет':    
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет, {self.params["name"]}!')
                    if  self.params['city'] is None:  
                        self.message_send(event.user_id, 
                                          f'''Для начала работы бота, введите 
                                          название Вашего города или укажите его
                                          в своем профиле''')
 
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                if event.text.isalpha() and len(event.text) > 1:
                                    self.params['city'] = event.text.lower()
                                    self.message_send(
                                        event.user_id, 
                                        f'Ваш город: {self.params["city"].capitalize()}\n' 
                                        'Нажмите "старт" для запуска бота')
                                else:
                                     self.message_send(
                                        event.user_id, 
                                        f'''Такого города не существует! 
                                        Введите название вашего города''')
                                     continue
                                break                        
                                                    
                    elif  self.params['year'] is None:  
                        self.message_send(event.user_id, 
                                          f'Укажите Ваш возраст(число)')    
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                if event.text.isdigit() and int(event.text) > 17:
                                    self.params['year'] = event.text
                                    self.message_send(
                                        event.user_id, 
                                        f'Ваш возраст: {self.params["year"]}\n\n'
                                        'Нажмите "старт" для запуска бота')
                                else:
                                     self.message_send(
                                        event.user_id, 
                                        f'Укажите число!')
                                     continue
                                break      

                elif event.text.lower() == 'старт':
                        self.message_send(
                        event.user_id, f'Привет, {self.params["name"]}!\n\n'
                        'Чтобы начать искать анкеты, введите комманду "поиск"\n' 
                        'Чтобы завершить работу, введите комманду "завершить"')
                
                elif event.text.lower() == 'поиск':
                  #   поиск анкет
                  
                    self.message_send(
                        event.user_id, 'Готово. Ищем дальше?')
                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(
                            self.params, self.offset)

                        worksheet = self.worksheets.pop()                   
                        # проверка анкеты в бд. Если анкет в списке больше нуля, 
                        # то проверяем наличие выбранной анкеты в списке
                        
                        while check_user(engine, event.user_id, worksheet['id']):
                           if len(self.worksheets) > 0:
                              worksheet = self.worksheets.pop()
                           else:
                              break
                           
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        self.offset += 10

                    self.message_send(
                        event.user_id,
                        f'Имя: {worksheet["name"]} ссылка: vk.com/id{worksheet["id"]}',
                        attachment=photo_string
                    )
                    
                    'добавление в бд '
                    if check_user(engine, event.user_id, worksheet['id']) is False:
                           add_user(engine, event.user_id, worksheet['id'])   
                              
                elif event.text.lower() == 'завершить':
                    self.message_send(
                        event.user_id, 'До свидания!\n\n'
                        'Чтобы снова запустить бот, введите комманду "привет"')
                    
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')
    

if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
    