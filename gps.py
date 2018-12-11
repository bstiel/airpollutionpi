import logging


logger = logging.getLogger(__name__)


def parse(data):
    if data[0:6] == "$GPRMC":
        sdata = data.split(",")
        if sdata[2] == 'V':
            logger.warning('No satellite data available')
            return
        logger.debug('Parse GPRMC')
        time = sdata[1][0:2] + ":" + sdata[1][2:4] + ":" + sdata[1][4:6]
        lat = sdata[3]
        north_south = sdata[4] # latitude direction N/S
        lon = sdata[5] # longitute
        east_west = sdata[6] #longitude direction E/W
        speed = sdata[7] #Speed in knots
        tr_course = sdata[8] # True course
        timestamp = "20" + sdata[9][4:6] + "-" + sdata[9][2:4] + "-" + sdata[9][0:2] + "T" + time
        return {
            'timestamp': timestamp,
            'lat': float(lat) * (-1 if north_south == 'S' else 1),
            'lon': float(lon) * (-1 if east_west == 'W' else 1),
            'speed': float(speed),
            'tc': tr_course
        }