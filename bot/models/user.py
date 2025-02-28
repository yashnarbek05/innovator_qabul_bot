class User:
    def __init__(self, number, fullname, age, work_place, email, hudud, direction, user_photo, offers, language):
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

    def get_fullname(self):
        return self._fullname

    def get_number(self):
        return self._number

    def get_age(self):
        return self._age

    def get_user_photo(self):
        return self._user_photo

    def get_work_place(self):
        return self._work_place

    def get_language(self):
        return self._language

    def get_offers(self):
        return self._offers

    def get_hudud(self):
        return self._hudud
    
    def get_direction(self):
        return self._direction
    
    def get_email(self):
        return self._email
