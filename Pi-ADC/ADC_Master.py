import time
import threading
import datetime
import csv
import ADC_Conveter as ADC

#---------------------------------------------------------------------------------------------
T0Kick = False       #stable timer kicked
TsEnd = False        #collector finished
inSignal = []        #collect data list
bufSignal = []

smpPeriod = 0.02     #sample period in sec
chkPeriod = 0.001    #check period in sec
dlyPeriod = 0.1

port = 0             #SPI0 of P3
device = 0           #CE0 of P3
adCh = [0, 1, 2, 3]  #Ad channels of MCP3008
duration = 10        #max collection time in sec
tgtCh = 0            #target detect channel
tgtLevel = 1.8       #target trigger level

maxCnt = int(duration/smpPeriod)

#--------------------------------------------------------------------------------------------
# Enable a stable time to triger data collection
#--------------------------------------------------------------------------------------------            
class T0(object):
    
    def __init__(self, period):
        self.pd = period
    
    def run(self):
        global T0Kick
        while (True):
            T0Kick = True       #enable to collect data
            time.sleep(self.pd)

#--------------------------------------------------------------------------------------------
#collect data from SPI channel
#--------------------------------------------------------------------------------------------            
class Tcol(object):
    
    def __init__(self, port, device, ch, period, count):
        self.adc = ADC.ADConverter(port, device)
        self.ch = ch
        self.pd = period
        self.mx = count
        self.paused = False
        self.state = threading.Condition()
    
    def run(self):
        global T0Kick
        global inSignal
        global bufSignal
        global TsEnd

        self.resume() # unpause self
        
        while True:
            with self.state:
                if self.paused:
                    self.state.wait() # block until notified

            cnt = 0
            inSignal=[]
            inSignal.append([])
            while cnt < self.mx:   # maximum amount of data collection 
                if T0Kick == True:
                    for i in self.ch:
                        value = self.adc.readADC(i)
                        inSignal[cnt].append(self.adc.convertVolts(value, 4))
                    T0Kick = False   # finish this time collection
                    cnt = cnt+1
                    inSignal.append([])
                    #print(cnt,': ', signal)

                time.sleep(self.pd)
            TsEnd = True
            bufSignal = inSignal  # bufferred the in signal
            #self.pause()  #set the timer to be paused

    def resume(self):
        with self.state:
            self.paused = False
            self.state.notify()  # unblock self if waiting
        #print('Data collector being resumed!')

    def pause(self):
        with self.state:
            self.paused = True  # make self block and wait
        #print('Data collector being paused!')

#----------------------------------------------------------------------------------------------
def saveRec(mode, tCh, tLevel):

    acctL = 0
    if mode == 'lt': # level threshold mode          
        for i in range(len(bufSignal)-1):
            if bufSignal[i][tCh] > tLevel:
                acctL = acctL+1
    if acctL > 3 or mode == 'tb':   #tb: time based mode
        # write a csv file
        
        ts = datetime.datetime.now()
        fileName = ts.isoformat() + '.csv'
        with open(fileName, 'a', newline='') as f1:        
            rowdata = csv.writer(f1, delimiter=',')
            for i in range(len(bufSignal)-1):
                #print(signal[i])
                rowdata.writerow(bufSignal[i])
        tf = datetime.datetime.now()
        print('time for saving: ',  tf-ts)
        return(True)
    else:
        return(False)

#------------------------------------------------------------------------------------------------        
if __name__ == '__main__':

    t0 = T0(smpPeriod)
    mt = threading.Thread(target = t0.run,  args=())

    tcol = Tcol(port, device, adCh, chkPeriod, maxCnt)
    pt = threading.Thread(target = tcol.run,  args=())
    pt.start()  # start the collection
    
    flag = False
    mt.start()  # start the triger timer
    while flag == False:

        ts = datetime.datetime.now()
        TsEnd = False
        #tcol.resume()  # resume the timer if needed
        while TsEnd == False:  #wait for finish
            time.sleep(chkPeriod)
    
        tf = datetime.datetime.now()
        print('time for collection: ',  tf-ts)
        
        #level triggered, detect channel 0, trigger level > threshold
        if(saveRec(mode='lt', tCh=tgtCh, tLevel=tgtLevel) == True):
            print('next run..')
        time.sleep(chkPeriod)
