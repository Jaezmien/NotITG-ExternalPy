show_heartbeat_message = False
# If you use a different file name, enable this.
# You will still need to make sure that build is a released build, however.
# This will loop through all active programs, and detect if an address is returning a build date.
unknown_nitg_filename = False

## NOTITG EXTERNAL
import notitg as NITGEXT
cont_exit = False
encode_guide = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n'\"~!@#$%^&*()<>/-=_+[]:;.,`{}"
notitg_appid = 1
def encode_string(str):
    buff = []
    for i in range(len(str)):
        buff.append( encode_guide.find(str[i]) )
    return buff
def decode_buffer(buff):
    str = ""
    for x in buff:
        str += encode_guide[x - 1]
    return str
rpc_screen = None
def notitg_onRead(buffer):
    pass

## NOTITG HANDLER
import time
import textwrap # just because
from apscheduler.schedulers.background import BackgroundScheduler
sched = BackgroundScheduler()
nitg: NITGEXT.NotITG = None
has_notitg = False
notitg_writeBuffer = []
notitg_readBuffer = []
# https://stackoverflow.com/a/312464
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
def WriteNotITG(buffer):
    global notitg_writeBuffer
    if len( buffer ) <= 26:
        notitg_writeBuffer.append({
            "buffer": buffer,
            "set": 0,
        })
    else:
        buffer_chunks = list( chunks(buffer, 26) )
        for i in range(len(buffer_chunks)):
            notitg_writeBuffer.append({
                "buffer": buffer_chunks[i],
                "set": 2 if len(buffer_chunks) == (i+1) else 1
            })
def TickNotITG():
    global has_notitg
    global nitg
    global notitg_readBuffer
    global notitg_writeBuffer
    if has_notitg:
        if nitg.GetExternal(57)==1 and nitg.GetExternal(59)==notitg_appid:
            read_buffer = []
            
            for i in range(28,28 + nitg.GetExternal(54)):
                read_buffer.append(nitg.GetExternal(i))
                nitg.SetExternal(i,0)
            
            if nitg.GetExternal(55) == 0:
                notitg_onRead( read_buffer )
            else:
                notitg_readBuffer.extend( read_buffer )
                if nitg.GetExternal(55) == 2:
                    notitg_onRead( notitg_readBuffer )
                    notitg_readBuffer.clear()

            nitg.SetExternal(54,0)
            nitg.SetExternal(55,0)
            nitg.SetExternal(59,0)
            nitg.SetExternal(57,0)
        if len( notitg_writeBuffer ) > 0 and nitg.GetExternal(56)==0:
            nitg.SetExternal(56,1)
            write_buffer = notitg_writeBuffer.pop(0)
            index = 0
            for x in write_buffer['buffer']:
                nitg.SetExternal( index , x )
                index += 1 # No i++ but i'll take it
            nitg.SetExternal(26,len(write_buffer['buffer']))
            nitg.SetExternal(27,write_buffer['set'])
            nitg.SetExternal(56,2)
            nitg.SetExternal(58,notitg_appid)

def HeartbeatNotITG():
    global has_notitg
    global nitg
    if has_notitg:
        if NITGEXT.Heartbeat(nitg):
            if show_heartbeat_message: print('💓  Successfully heartbeated NotITG!')
        else:
            has_notitg = False
            print('⚠️  Cannot heartbeat NotITG. Retrying in 5 seconds.')
    else:
        try:
            nitg = NITGEXT.Scan( not unknown_nitg_filename )
            if nitg.version == "V1" or nitg.version == "V2":
                print('⚠️  Unsupported NotITG version. Found: {0}, expected V3 or higher. Retrying in 5 seconds.'.format(nitg.version))
            elif nitg.GetExternal(60)==0:
                print('⌛  NotITG found, but still initializing. Retrying in 5 seconds.')
            else:
                print(textwrap.dedent("""\
                    ✔️  NotITG Found!
                    > -------------------------------
                    >>  Version: {0}
                    >>  Build Date: {1}
                    > -------------------------------""".format(nitg.version,nitg.details['BuildDate'])))
                has_notitg = True
                time.sleep(0.5)
                WriteNotITG([0,1])
        except NITGEXT.NotITGError:
            print('⚠️  Can\'t find NotITG, retrying in 5 seconds.')
sched.add_job(HeartbeatNotITG, 'interval', seconds=5, id='Heartbeat')
if unknown_nitg_filename:
    print('❗  Brute-forcing detection!')
HeartbeatNotITG()
#tick_job = sched.add_job(TickNotITG, 'interval', seconds=0.1, id='Tick') # Will fuck up if it the function is slow
sched.start()
while not cont_exit:
    TickNotITG()
    time.sleep(0.1)