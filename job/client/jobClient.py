import os
import commands
import re
import time

#Add helper libraries
import sys
sys.path.insert(0, "../../classes")
import client_class, protocols

class ClientJob(client_class.Client):

    def __init__(self):
        super(ClientJob, self).__init__()

    def doJob(self):
        # Receive job
        if not self.connect("file",  protocols.ProtocolFile._JOB_NEW, jobDirectory=os.path.join(os.getcwd(), "jobs"), host="savannah.cs.gwu.edu"):
            return False

        # Get newest file in 'jobs/' directory
        filename = max(map(lambda file: "jobs/" + file,
                           os.listdir("jobs/")),
                       key=lambda file : os.path.getmtime(file))

        # Untar file
        commands.getoutput("tar xzf " + filename)
        
        # Run job
        ID = re.compile(r"jobs\/(.+)\.recv").findall(filename)[0]
        commands.getoutput("jobs/%s/job < jobs/%s/jobInput > jobs/%s.send" % (ID, ID, ID))
        
        # Clean up job
        commands.getoutput("rm -rf %s jobs/%s" % (filename, ID))

        # Send output back
        self.connect("file", protocols.ProtocolFile._JOB_OLD, jobDirectory=os.path.join(os.getcwd(), "jobs"), jobID=int(ID), host="savannah.cs.gwu.edu")

def Main():
    client = ClientJob()

    try:
        while True:
            client.doJob()
            time.sleep(1)
    except KeyboardInterrupt:
        print "Exiting..."

if __name__ == "__main__":
    Main()
