class User:
    def __init__(self, chat_id, date, number, fullname, age, work_place, email, hudud, direction, user_photo, offers, language):
        self._chat_id = chat_id
        self._date = date
        self._number = number
        self._fullname = fullname
        self._age = age
        self._work_place = work_place
        self._email = email
        self._user_photo = user_photo
        self._hudud = hudud
        self._direction = direction
        self._offers = offers
        self._language = language

    def get_chat_id(self):
        return self._chat_id

    def get_date(self):
        return self._date

    def get_number(self):
        return self._number

    def get_fullname(self):
        return self._fullname

    def get_age(self):
        return self._age

    def get_work_place(self):
        return self._work_place

    def get_email(self):
        return self._email

    def get_user_photo(self):
        return self._user_photo

    def get_hudud(self):
        return self._hudud

    def get_direction(self):
        return self._direction

    def get_offers(self):
        return self._offers

    def get_language(self):
        return self._language



    def to_list(self):
        """Convert user object to a list for Google Sheets"""
        return [
            self._date, self._number, self._fullname, self._age, 
            self._work_place, self._email, self._hudud, self._direction, self._offers
        ]