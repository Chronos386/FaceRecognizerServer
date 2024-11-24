from datetime import datetime


def getWeekDayByDate(date: datetime) -> str:
    week_list = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    day_of_week = date.weekday()
    return week_list[day_of_week]
