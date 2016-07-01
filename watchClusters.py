from twilio.rest import TwilioRestClient
import subprocess
import sys
from time import sleep

def main():
    """
    Updates a pair of webpages on my UCL site with qstat output from UCL HEP and Legion clusters.
    Also uses twilio to send an SMS message when a set of jobs on a cluster goes from > 0 to 0.
    (Install in local hep area with pip install --user twilio)
    Note to future self: Make sure the hep cluster ssh public key is in the legion authorized keys then do:
      screen
      exec ssh-agent bash -l
      ssh-add
      run this python script!
    """

    updateEvery = 5 * 60 # in seconds

    # Read private things from local files so they're not on github
    # [:-1] to remove newline characters
    with file('account_sid', 'r') as fac:
        account_sid = fac.readline().replace('\n', '')
        print account_sid
    with file('auth_token', 'r') as fat:
        auth_token = fat.readline().replace('\n', '')
        print auth_token
    with file('my_number', 'r') as fmn:
        my_number = fmn.readline().replace('\n', '')
        print my_number
    with file('twilio_number', 'r') as ftn:
        twilio_number = ftn.readline().replace('\n', '')
        print twilio_number
    with file('hep_username', 'r') as fhu:
        hep_username = fhu.readline().replace('\n', '')
        print hep_username
    with file('ucl_username', 'r') as fuu:
        ucl_username = fuu.readline().replace('\n', '')
        print ucl_username

    # For SMS messaging
    client = TwilioRestClient(account_sid, auth_token)
    
    # Job counter variable 
    numJobsThisTime = [0, 0]
    numJobsLastTime = [0, 0]

    batchCommand = ["qstat", "-u", hep_username]
    legionCommand = ["ssh", ucl_username + "@legion.rc.ucl.ac.uk", "qstat -u " + ucl_username]

    commands = [batchCommand, legionCommand]

    # Follow symlinks to web pages
    outFileNames = ['/home/'+hep_username+'/Sites/'+hep_username+'/batch/current.txt',
                   '/home/'+hep_username+'/Sites/'+hep_username+'/legion/current.txt']

    print outFileNames

    # For the sms notification
    clusterNames = ['HEP', 'Legion']

    while True:

        # i is an index over batch/legion
        for i, command in enumerate(commands):

            # print command
            ssh = subprocess.Popen(command,
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

            result = ssh.stdout.readlines()
	    if result == []:
	        error = ssh.stderr.readlines()

                # If the result is blank with no error, then it's just that there are no jobs
	        if not error == []:

                    # Here we attempt to handle the case where we get an error from ssh
	            sshError = False
	            for er in error:
	                if 'ssh' in er:
	                    sshError = True

	            # Here we try and handle it by saying that the jobs were never started.
	            if sshError is True:
                        numJobsLastTime[i] = 0
	                pass
                    # Otherwise print it to the screen and get ready to add more error handling.
	            else:
	                print >>sys.stderr, "ERROR: %s" % error
	
	    numJobsThisTime[i] = len(result)
	    with file(outFileNames[i], 'w') as f:
	            
	        # print numJobsThisTime
	                
	        for line in result:
	            #print line[:-1]
	            f.write(line)
	
	    if numJobsLastTime[i] > 0 and numJobsThisTime[i] == 0:
	        #print 'Sending message'
                messageBody = 'Your jobs on the ' + clusterNames[i] + ' cluster are complete!'
                message = client.messages.create(to = my_number,
                                                 from_ = twilio_number,
                                                 body = messageBody)

	    elif numJobsThisTime[i] > 0:
	        # print 'Jobs in progess, not done yet'                
                pass
            else:
	        # print 'No jobs running'                
                pass

            # print numJobsLastTime[i], numJobsThisTime[i]
	    numJobsLastTime[i] = numJobsThisTime[i]

	sleep(updateEvery)

if __name__ == '__main__':
    main()
