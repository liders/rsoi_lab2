$python db.py
$ipython
>db.client.insert('CC5342E7E97055FBA2815F7D30CED0010092C0C5DCBE1366C1CD4CFF48E63CD7A8A8CC577088ED47C22CD5184899748BE33BF32291AE415FE83AC547726B44E4', 'https://www.yandex.com', 'app1')
>db.client.commit()

db.event.insert('Конценрт Imagine Dragons', '2016-01-24', 'Ещё каких-то пять лет назад квартет из Лас-Вегаса был известен разве что своим друзьям. Сегодня они — мировые звёзды первой величины, которые с лёгкостью заполняют стадионы, оккупируют все мыслимые музыкальные чарты и демонстрируют эталонное качество света и звука на каждом выступлении. Композиции Imagine Dragons наносят множественные сокрушительные удары по органам чувств, заставляя забыть о существовании стилистических границ. Романтические баллады плавно перетекают в альтернативный драйв, сменяющийся напористым хоровым пением и уходящий в зубодробительный дабстеп. Это музыка кардинально нового порядка, авторы которой мыслят исключительно масштабными категориями.', 'Олимпийский')
db.event.insert('Ногу Свело!', '2016-01-29', 'Один из самых востребованных хедлайнеров в истории отечественных рок-фестивалей, столичная группа "Ногу Cвело!" на виду с конца 1980-х, но оборотов не сбавляет - несмотря на многочисленные сторонние активности своего неутомимого фронтмена Макса Покровского (не так давно сочинившего песню для, страшно сказать, Иосифа Кобзона.', 'Концертный зал 1')
db.event.insert('Ногу Свело!', '2016-01-21', 'Один из самых востребованных хедлайнеров в истории отечественных рок-фестивалей, столичная группа "Ногу Cвело!" на виду с конца 1980-х, но оборотов не сбавляет - несмотря на многочисленные сторонние активности своего неутомимого фронтмена Макса Покровского (не так давно сочинившего песню для, страшно сказать, Иосифа Кобзона.', 'Концертный зал 1')
db.event.insert('Валентин Серов. К 150-летию со дня рождения', '2016-01-28', 'Третьяковская галерея представляет самый ожидаемый проект года — выставку произведений Валентина Александровича Серова (1865–1911), одного из наиболее любимых русских художников, крупнейшей и ключевой фигуры своего времени.', 'Третьяковская галерея на Крымском Валу')
db.client.commit()


в браузере переходим по адресу:
http://localhost:5050/register
http://localhost:5050/oauth/authorize?response_type=code&client_id=0&state=no_state

Далее с полученным code делаем POST запрос
на localhost:5050/oauth/token с параметрами
grant_type = [authorization_code, refresh_token]
code
client_id
client_secret

---POST CREATE BID-----
curl -H "Authorization: Bearer 7f74b4d26d05103fe14ffd7215f50245f964faaed2178403dd0ab989b437dbc3" \
-X POST http://localhost:5050/bids/ \
-d '{"number_tickets": 12, "event": {"id": 6}}'

-----POST REFRESH TOKEN-----------
curl -X POST localhost:5050/oauth/token --data 'grant_type=refresh_token&grant_type=refresh_token&client_id=0&refresh_token=fc48f401c08b754b1652960d19577cb8c239024f5c228b8ab83e4ca6a9671edf&client_secret=CC5342E7E97055FBA2815F7D30CED0010092C0C5DCBE1366C1CD4CFF48E63CD7A8A8CC577088ED47C22CD5184899748BE33BF32291AE415FE83AC547726B44E4'

-----POST TOKEN
curl -X POST localhost:5050/oauth/token --data 'code=<code>&grant_type=authorization_code&grant_type=refresh_token&client_id=0&client_secret=CC5342E7E97055FBA2815F7D30CED0010092C0C5DCBE1366C1CD4CFF48E63CD7A8A8CC577088ED47C22CD5184899748BE33BF32291AE415FE83AC547726B44E4'

-------PUT BID
curl -H "Authorization: Bearer 7f74b4d26d05103fe14ffd7215f50245f964faaed2178403dd0ab989b437dbc3" \
-X PUT http://localhost:5050/bids/5 \
-d '{"number_tickets": 4, "event": {"id": 6}}'

----DELETE BID
curl -H "Authorization: Bearer 7f74b4d26d05103fe14ffd7215f50245f964faaed2178403dd0ab989b437dbc3" \
-X DELETE http://localhost:5050/bids/6

------GET BID
curl -H "Authorization: Bearer 7f74b4d26d05103fe14ffd7215f50245f964faaed2178403dd0ab989b437dbc3" \
-X GET http://localhost:5050/bids/

{"access_token": "7f74b4d26d05103fe14ffd7215f50245f964faaed2178403dd0ab989b437dbc3", "token_type": "bearer", "expires_in": 3600, "refresh_token": "2e94e53831b960c518b8fc9de7cfcbe5b14b84378c7c46f74480c98564ed2c68"}