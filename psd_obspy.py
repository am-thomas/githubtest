import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from obspy.signal import PPSD
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
client = Client('IRIS')

#Set station parameters
net = "NW"
sta = "HQIL"
loc = "00"

#Times from 3 am on a weekday (non-holiday)
time_3wkday = ['2014-03-12T08:02:00','2014-07-21T08:00:00',
              '2014-09-18T08:05:00','2014-12-10T09:09:00',
              '2015-03-13T08:11:00','2015-06-09T08:02:00',
              '2015-09-24T08:04:00','2015-12-11T09:08:00',
              '2016-03-09T09:03:00','2016-06-23T08:00:00',
              '2016-08-15T08:09:00','2016-11-16T09:07:00']

def plot_split(utc_starttime, plot_chan, n_segments=4, total_duration=20):
    starttime = UTCDateTime(utc_starttime)
    endtime = UTCDateTime(utc_starttime) + total_duration * 60
    int_segment = (endtime - starttime) / n_segments

    inv = client.get_stations(network=net, station=sta, channel=plot_chan, level="response", starttime=starttime)


    # Get waveform for each orientation and create a composite list
    st_HH1 = client.get_waveforms(net, sta, loc, 'HH1', starttime, endtime)
    st_HH2 = client.get_waveforms(net, sta, loc, 'HH2', starttime, endtime)
    st_HHZ = client.get_waveforms(net, sta, loc, 'HHZ', starttime, endtime)
    st_list = [st_HH1, st_HH2, st_HHZ]

    #Trim each stream object into the given number of segments and create a superlist containing
    #lists of trimmed objects for each channel in the order [HH1,HH2,HHZ]
    st_trim_slist = []
    for st in st_list:
        starttime_trim = starttime
        st_trim_chan = []
        for i in range(4):
            endtime_trim = starttime_trim + int_segment
            st_trim = st.copy()
            st_trim.trim(starttime=starttime_trim, endtime=endtime_trim)
            st_trim_chan.append(st_trim)
            starttime_trim = starttime_trim + int_segment
        st_trim_slist.append(st_trim_chan)

    #Create new superlists with waveforms corrected for stage 0 sensitivity and their coressponding times
    tr_trim_slist = []
    tr_times_slist = []
    for list in st_trim_slist:
        tr_trim_chan = []
        tr_time_chan = []
        for st_trim in list:
            tr_trim = st_trim[0].data / 9.43695e8
            time = st_trim[0].times(type='matplotlib')
            tr_trim_chan.append(tr_trim)
            tr_time_chan.append(time)
        tr_trim_slist.append(tr_trim_chan)
        tr_times_slist.append(tr_time_chan)

    #Plot each trimed segment in the desired channel
    fig, ax1 = plt.subplots(4, 1, figsize=(6, 6))
    chan_index_dict = {'HH1':0, 'HH2':1, 'HHZ':2 }
    chan_index = chan_index_dict[plot_chan]
    tr_trim_plot = tr_trim_slist[chan_index]
    tr_times_plot = tr_times_slist[chan_index]
    st_trim_plot = st_trim_slist[chan_index]

    for i in range(len(tr_trim_plot)):
        ax1[i].plot(tr_times_plot[i], tr_trim_plot[i], color ='black')
        locator = ax1[i].xaxis.set_major_locator(mdates.AutoDateLocator())
        ax1[i].xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax1[i].set_xlim([tr_times_plot[i][0], tr_times_plot[i][-1]])
        ax1[i].set_ylabel('M/S')
    ax1[len(tr_trim_plot)-1].set_xlabel('UTC Time')
    plt.show()

    #Plot the PSD (uncorrected for stage 0 sensitivity) of each trimmed segment using obspy
    for i in range(len(st_trim_plot)):
        ppsd = PPSD(st_trim_plot[i][0].stats, metadata=inv, ppsd_length=60 * 5)
        ppsd.add(st_trim_plot[i][0])
        ppsd.plot()
    plt.show()

if __name__ == '__main__':
    starttime = time_3wkday[1]
    plot_split(starttime, plot_chan='HH1')
