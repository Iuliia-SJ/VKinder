from pprint import pprint
from datetime import datetime
# импорты
import vk_api
from vk_api.exceptions import ApiError

from config import acces_token


# получение данных о пользователе


class VkTools:
    def __init__(self, acces_token):
        self.vkapi = vk_api.VkApi(token=acces_token)
        
    def _bdate_toyear(self, bdate):
        user_year = bdate.split('.')[2]
        now = datetime.now().year
        return now - int(user_year)

    def get_profile_info(self, user_id):

        try:
            info, = self.vkapi.method('users.get',
                                      {'user_id': user_id,
                                       'fields': 'city,sex,relation,bdate'
                                       }
                                      )
            
               
        except ApiError as e:
            info = {}
            print(f'error = {e}')

        result = {'name': (info['first_name'] + ' ' + info['last_name']) if
                  'first_name' in info and 'last_name' in info else None,
                  'sex': info.get('sex'),
                  'city': info.get('city')['title'] if info.get('city') is not None else None,
                  'year': self._bdate_toyear(info.get('bdate'))
                  } 

        return result
     
      # поиск анкет
    def search_worksheet(self, params, offset):
        try:
            users = self.vkapi.method('users.search',
                                      {
                                          'count': 10,
                                          'offset': offset,
                                          'hometown': params['city'],
                                          'sex': 1 if params['sex'] == 2 else 2,
                                          'has_photo': True,
                                          'age_from': params['year'] - 3,
                                          'age_to': params['year'] + 5,
                                      }
                                      )
        except ApiError as e:
            users = []
            print(f'error = {e}')

        result = [{'name': item['first_name'] + ' '+ item['last_name'],
                   'id': item['id']
                   } for item in users['items'] if item['is_closed'] is False
                  ]

        return result
    
    # функция поиска города из базы ВК
    # def find_city(self, q: str):
    #     city = self.vkapi.method('database.getCities',
    #                                    {'country_id': 1,
    #                                     'q': q,
    #                                     'count': 1
    #                                     })
    #     city_id = city['items'][0]['id']
    #     return city_id 
        
      # функция демонстрации фото
      
    def get_photos(self, id):
        try:
            photos = self.vkapi.method('photos.get',
                                       {'owner_id': id,
                                        'album_id': 'profile',
                                        'extended': 1
                                        }
                                       )
        except ApiError as e:
            photos = {}
            print(f'error = {e}')

        result = [{'owner_id': item['owner_id'],
                   'id': item['id'],
                   'likes': item['likes']['count'],
                   'comments': item['comments']['count']
                   } for item in photos['items']
                  ]
      #   сортировка фото по лайкам и комментам
        result.sort(key=lambda x: x['likes']+x['comments'], reverse=True) 
        
        return result[:3]


if __name__ == '__main__':
    user_id = 475689978
    tools = VkTools(acces_token)
    params = tools.get_profile_info(user_id)
    worksheets = tools.search_worksheet(params, 20)
    worksheet = worksheets.pop()
    photos = tools.get_photos(worksheet['id'])
    # my_hometown = tools.find_city('hometown')
    pprint(worksheets)
