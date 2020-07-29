import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.animation as anim 
import matplotlib.colors as cols
import numpy as np 
import json
import geopandas as gdp
import math

framesPerDay = 4
daysPadding = 5

windArrowSpacing = 0.04
windArrowSize = 0.01

padding = 0.05
daysReportShown = 4

siteLocation = (-76.94558, 42.84081)

reportLocationsDates = pd.read_csv("data/HABreports_2019.csv", parse_dates=["SAMPLE_DATE"])
reportLocationsDates = reportLocationsDates.sort_values('SAMPLE_DATE')
#convert to geopandas
gpdReports = gdp.GeoDataFrame(reportLocationsDates, geometry=gdp.points_from_xy(reportLocationsDates.Longitude, reportLocationsDates.Latitude))


#numbers correspond to cmap 
def getPointColor (val):
    if val == "NO_BLOOM":
        return 0
    elif val == "SUSPICIOUS":
        return 0.4
    elif val == "CONFIRMED":
        return 0.6
    elif val == "CONFIRMED_WITH_HIGH_TOXINS":
        return 1

#add column for color map value
gpdReports['color'] = gpdReports["HAB_STATUS"].apply(getPointColor)


windData = pd.read_csv("data/WindSpeedDirection.txt", delimiter="\t", header=28, skiprows=[29], parse_dates=["datetime"])
windData = windData.rename(columns={"250182_00036":"WIND_DIR", "251357_62625":"WIND_SPEED"})
#get first and last date of HABs reports
firstDate = np.datetime64(gpdReports['SAMPLE_DATE'].iloc[0]) - np.timedelta64(daysPadding, 'D')
lastDate = np.datetime64(gpdReports['SAMPLE_DATE'].iloc[-1]) + np.timedelta64(daysPadding, 'D')

timeOffset = lastDate - firstDate
totalDays = timeOffset.astype('timedelta64[D]') / np.timedelta64(1, 'D')
totalFrames = int(totalDays * framesPerDay)
lakeBoundaryGeo = gdp.read_file("data/SenecaBoundary.geojson")

lakePolygon = lakeBoundaryGeo['geometry'].iloc[0]
gpdReports["InPoly"] = gpdReports.within(lakePolygon)

gpdReports = gpdReports[gpdReports.InPoly == True]

print (gpdReports)


lakeBounds = lakeBoundaryGeo.bounds
fig = plt.figure()
minx = lakeBounds["minx"][0] - padding
maxx = lakeBounds["maxx"][0] + padding
miny = lakeBounds["miny"][0] - padding
maxy = lakeBounds["maxy"][0] + padding

colorMap = cols.ListedColormap(["blue", "yellow", "orange", "red"])

mainAx = plt.axes(xlim = (minx, maxx), ylim = (miny, maxy))
lakeBoundaryGeo.boundary.plot(ax=mainAx)
reportPoints = mainAx.scatter([], [], c=[], cmap=colorMap, vmin=0, vmax=1)
dateText = mainAx.text((minx + maxx)/2, miny + padding/2, "", horizontalalignment='center')
plt.title("Seneca Lake HABS Reports 2019")

windArrow, = plt.plot([], [], lw=2, color='red')

""" def updateArrows (angle, magnitude):
    for arrow in windArrows:
        arrow.remove()
    for x in np.arange(minx + padding/2, maxx - padding/2, windArrowSpacing):
        for y in np.arange(miny + padding/2, maxy - padding/2, windArrowSpacing):
            arrow = mainAx.arrow(x,y,windArrowSize, 0, width = 0.0001, head_width=0.003)
            windArrows.append(arrow) """

#mainAx.scatter(df['Longitude'].tolist(), df['Latitude'].tolist())

def init ():
    reportPoints.set_offsets([])
    reportPoints.set_array([])
    dateText.set_text("")
    modified = [reportPoints, dateText, windArrow]
    #modified.extend(windArrows)
    windArrow.set_data([], [])
    return modified

def animate(i):
    frameStartDate = firstDate + i * np.timedelta64(int(24 / framesPerDay), 'h')
    frameEndDate = frameStartDate + np.timedelta64(daysReportShown, 'D')
    frameDateMask = (gpdReports['SAMPLE_DATE'] > frameStartDate) & (gpdReports['SAMPLE_DATE'] <= frameEndDate)
    gpdReportsMasked = gpdReports.loc[frameDateMask]

    scatterX = gpdReportsMasked["Longitude"].tolist()
    scatterY = gpdReportsMasked["Latitude"].tolist()
    colors = np.array(gpdReportsMasked["color"], dtype="float")
    #print(colors)
    new_data = np.c_[scatterX, scatterY]
    reportPoints.set_offsets(new_data)
    reportPoints.set_array(colors)

    dateString = pd.to_datetime(frameStartDate).strftime('%m/%d/%Y')
    dateText.set_text(dateString)

    modified = [reportPoints, dateText, windArrow]
    #modified.extend(windArrows)

    mostRecentWindDataRow = -1
    windDataDates = windData["datetime"]
    for ind, date in enumerate(windDataDates):
        thisDate = np.datetime64(date)
        if thisDate > frameStartDate:
            mostRecentWindDataRow = ind - 1
            break

    #ensure that the last wind data is valid, i.e. greater than the date of the current frame
    if mostRecentWindDataRow > 0:
        #updateArrows(windData["WIND_DIR"].iloc(mostRecentWindDataRow), windData["WIND_SPEED"].iloc(mostRecentWindDataRow))
        lastAngle = windData["WIND_DIR"].iloc[mostRecentWindDataRow-1]
        angle = windData["WIND_DIR"].iloc[mostRecentWindDataRow]
        angle = (angle + lastAngle)/2
        speed = windData["WIND_SPEED"].iloc[mostRecentWindDataRow]

        direction = (math.sin(math.radians(angle)), math.cos(math.radians(angle)))

        arrowx = [siteLocation[0], siteLocation[0] + direction[0] * speed * windArrowSize]
        arrowy = [siteLocation[1], siteLocation[1] + direction[1] * speed * windArrowSize]

        windArrow.set_data(arrowx, arrowy)

    return modified

#animate(400)

nim = anim.FuncAnimation(fig, animate, init_func=init, frames=totalFrames, interval=1, blit=True)

#anim.save('blipTest.mp4', writer='ffmpeg')
    #reportLocationsDates = reportLocationsDates[(reportLocationsDates['REPORT_DATE'] > '2000-6-1') & (reportLocationsDates['date'] <= '2000-6-10')]
#reportLocations.plot(x='Longitude', y='Latitude', ax=mainAx, kind='scatter')

plt.show()
