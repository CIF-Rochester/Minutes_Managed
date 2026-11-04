# Minutes Managed

CIF posts all of it's minutes onto its website, as, if you are looking at this repo, I am sure you are aware of.  

The minutes are displayed based off of what exists inside of a dedicated local "Minutes" directory inside of the Wordpress instance.  A PHP plugin pulls things from this directory, based off of how things are stored in that directory, and displays them on the website all nice and orderly-like

This provides the advantage of the minutes being incredibly portable, being able to be migrated, pulled, or moved around as need be.  

## Ok, so that's all well and good...

Well, with this new system arose a wee bit of a problem, how does one effectively get files *to* that local directory.  In the days of yore, users would upload HTML to wordpress (But, with the horrors that were migrating the old site to this one, we didn't want to do that again...).  I was just scp-ing things onto our web server (zeta), but this, too comes with a catch (Due to the way our network worked, you needed to scpu those files onto a server first, then onto the web server if you were not on a lab machine).  Whilst one could still do this, it seems unideal for someone who is not technically inclined.  

So, this created the need for this little project!  It's basically a mini version of the NFS drive feature of the New CIF Panel, allowing admins to log in, upload, and remove minutes from that local directory, from anywhere on the University Network.  Pretty cool, if I do say so myself.  : )

## Methodology, and setup. 

Due to some quirks of our network, the DMZ doesn't have direct access to much on the 220 (our standard vlan), which prevents users authenticating via LDAP, which in turn led to some creative solutions.  Namely, the program ssh-s into another server, which has access to those ports, to kinit, and check if the user is a member of the admins group.  If that script succeeds, the user is an admin, and are allowed to log in.  This script lies under `SECONDARY_SERVER`

This requires an SSH key, which you can create using the usual method, provided that a service account has been created on that secondary server.  I'd recommend creating a random password for this user.  Note that the private SSH key you create should go into the `PRIVATE` directory.  Put the script in `CHECKING_SERVER` directory into that created user's home directory.  

From there, all you should need do is make an `app.cfg` file (Based on `app_example.cfg`), configuring things properly, and edit scripts/check_admin.sh to make sure everything there is correct based on your setup.  

Remember to create a python virtual environment, and install flask.  It should be the only thing you need to install via pip.  

## Closing remarks

'Tis been fun.  : )



