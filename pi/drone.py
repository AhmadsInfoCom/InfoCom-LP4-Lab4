from flask import Flask, request
from flask_cors import CORS
import subprocess
import  requests
import os
from werkzeug import serving
import ssl

HTTPS_ENABLED = True
VERIFY_USER=True

SVR_CRT="../certs/drone1/drone1.crt"
SVR_KEY="../certs/drone1/drone1.key"
CA_CRT="../certs/CA/ca.crt"

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'dljsaklqk24e21cjn!Ew@@dsa5'


#Give a unique ID for the drone
#===================================================================
myID = "drone1"    #stod bara typ "MY_DRONE" från början
#===================================================================


# Get initial longitude and latitude the drone
#===================================================================


# r+  börjar läsa/skriva från början. om du läser först så skriver du på i slutet.
# a+ börjar läsa/skriva från slutet (så du kommer läsa en tom sträng hela tiden, även om du write och sen läser, så fattar inte poängen riktigt)
# w+ raderar innehållet sen börjar läsa/skriva från slutet (så du kommer läsa en tom sträng hela tiden, även om du write och sen läser, så fattar inte poängen riktigt)
# flowchart: https://stackoverflow.com/questions/21113919/difference-between-r-and-w-in-fopen#:~:text=%22w%2B%22%20Open%20a%20text%20file,if%20it%20does%20not%20exist.
# mer detaljerat: https://mkyong.com/python/python-difference-between-r-w-and-a-in-open/
# om att skriva i mitten av en fil: https://stackoverflow.com/questions/34467197/why-does-readline-put-the-file-pointer-at-the-end-of-the-file-in-python 

size = os.path.getsize("dronedestination.txt")
dronedest = open("dronedestination.txt", "r+")     #r+ allows append at start of file but if you read it once you will be at the end, a+ reads from end of file and appends to the end,    #står fel på följande länk om att a+ läser från start och skriver på slutet, jag testade och den läser från slutet också https://stackoverflow.com/questions/13248020/whats-the-difference-between-r-and-a-when-open-file-in-python
print(size)
if size > 0:     #om drönaren redan hade en position sist då vi stängde programmet
    linelist = dronedest.read().splitlines()                # readlines() kommer spara raderna med \n bakom, men read().splitline() gör så det sparas utan \n, https://stackoverflow.com/questions/15233340/getting-rid-of-n-when-using-readlines
    current_longitude = float(linelist[0])
    current_latitude = float(linelist[1])
else:             #annars skriver vi in initial coordinates i filen
    current_longitude = 13.21008 #rätt? stod 0 från början. hämtade från lp2 lab1 build.py, det var våra initial OSM coordinates då, de hette longitude och latitude.
    current_latitude = 55.71106 #samma som ovan.
    dronedest.writelines([str(current_longitude),'\n', str(current_latitude)])     #https://stackoverflow.com/questions/13730107/writelines-writes-lines-without-newline-just-fills-the-file    #https://stackoverflow.com/questions/51980776/python-readline-with-custom-delimiter
dronedest.close()

#===================================================================

drone_info = {'id': myID,
                'longitude': current_longitude,
                'latitude': current_latitude,
                'status': 'idle'
            }

# Fill in the IP address of server, and send the initial location of the drone to the SERVER
#===================================================================
SERVER= "http://100.100.100.24:5001/drone"
#bytte IP till den vi sätter på serverdrönaren (satte till 23, så drönarna kan vara 24 och 25), och porten till den som database ska köra på enligt README-filen.    #Stod från början: "http://SERVER_IP:PORT/drone"
with requests.Session() as session:
    resp = session.post(SERVER, json=drone_info)
#===================================================================

@app.route('/', methods=['POST'])
def main():
    coords = request.json
    # Get current longitude and latitude of the drone 
    #===================================================================
    dronedest = open('dronedestination.txt', 'r')
    #linelist = dronedest.readlines()
    linelist = dronedest.read().splitlines()
    current_longitude = float(linelist[0]) #?? hämta från textfilen som ni gjorde i simulator. Från instruktionerna till simulator.py:
    current_latitude = float(linelist[1]) #?? "The simulator moves the drone and stops when the drone arrives at to_location. You can save the final coordinates of the drone to a text file, so that the drone knows where it is and can start from this location as current_location for the next delivery.
    dronedest.close()
    #===================================================================
    from_coord = coords['from']
    to_coord = coords['to']
    subprocess.Popen(["python3", "simulator.py", '--clong', str(current_longitude), '--clat', str(current_latitude),
                                                 '--flong', str(from_coord[0]), '--flat', str(from_coord[1]),
                                                 '--tlong', str(to_coord[0]), '--tlat', str(to_coord[1]),
                                                 '--id', myID
                    ])
    return 'New route received'

if __name__ == '__main__':
    context = None
    print("Main is run.")
    #filecreationdebugging = open("/home/debuggingtestfile.txt", "x")
    if HTTPS_ENABLED:
        context = ssl.SSLContext() # alternativt:   ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        print("HTTPS is enabled, i.e. server needs to authenticate.")
    if VERIFY_USER:
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(CA_CRT)   #Vi litar på klienter med certifikat signerat av CA.
        print("Two-way HTTPS is enabled, i.e. client needs to authenticate as well.")
    try:
        context.load_cert_chain(SVR_CRT, SVR_KEY)
        print("Cert and key loaded into context.")
    except:
        print("Cert and key were not loaded into context for some reason.")
        #sys.exit("Error starting flask server, idk what we've done")
    #serving.run_simple("0.0.0.0", 5000, app, ssl_context=context)
    print("App is about to run. Hold on")
    app.run(debug=True, host='0.0.0.0', port='5000', ssl_context=context)
    print("We've come past 'app.run()' now.")
