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
        # lat = decode(sdata[3]) #latitude
        dir_lat = sdata[4]      #latitude direction N/S
        # lon = decode(sdata[5]) #longitute
        lon = sdata[5] #longitute
        dir_lon = sdata[6]      #longitude direction E/W
        speed = sdata[7]       #Speed in knots
        tr_course = sdata[8]    #True course
        date = sdata[9][0:2] + "/" + sdata[9][2:4] + "/" + sdata[9][4:6]#date
        return {
            'time': time,
            'lat': lat,
            'lon': lon,
            'dir_lat': dir_lat,
            'dir_lon': dir_lon,
            'speed': speed,
            'tc': tr_course,
            'date': date
        }

 
def decode(coord):
    #Converts DDDMM.MMMMM > DD deg MM.MMMMM min
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]
    return deg + " deg " + min + "." + tail + " min"