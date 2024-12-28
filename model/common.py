from datetime import datetime, timedelta


class Common:
    @staticmethod
    def get_timestamp(time: datetime = datetime.now()) -> float:
        return time.timestamp()

    @staticmethod
    def get_offset_time(offset: timedelta, time: datetime = datetime.now()) -> datetime:
        return time + offset
    
    @staticmethod
    def get_offset_timestamp(offset: timedelta, time: datetime = datetime.now()) -> float:
        return (time + offset).timestamp()