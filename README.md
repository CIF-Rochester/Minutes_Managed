# Minutes Managed

CIF posts all of it's minutes onto its website, as, if you are looking at this repo, I am sure you are aware of.  

The minutes are displayed based off of what exists inside of a dedicated local "Minutes" directory inside of the Wordpress instance.  A PHP plugin pulls things from this directory, based off of how things are stored in that directory, and displays them on the website all nice and orderly-like

This provides the advantage of the minutes being incredibly portable, being able to be migrated, pulled, or moved around as need be.  A much more elegant solution that had existed in the past.  

But, with this new system arose a wee bit of a problem, how does one effectively get files *to* that local directory?   

## Functionality

This site provides the following functionality,

- Admins can log into the application via their standard logins, authenticating against FreeIPA.  
- Admins can add minutes to the local "Minutes" directory to which is served by the website, individually, as a group, or as a folder
- Admins can remove minutes from the local "Minutes" directory, which is served by the website.  

## Why are the minutes set up this way?  

In the days of yore, users would upload HTML to wordpress (But, with the horrors that were migrating the old site to this one, we didn't want to do that again...).  Minutes prior to 2020 could simply be pulled from the Wordpress database with relative ease, though elements after that date had to be pulled manually... This new system doesn't have this problem, and can be moved to whatever system we so desire in the future.  Furthermore, minutes started to be taken in Word Documents at some point, which the old system simply could not support, leading to the present system

When the new website was created, I was just scp-ing things onto our web server (zeta), but this, comes with a catch (Due to the way our network worked, you needed to scp those files onto a server first, then onto the web server if you were not on a lab machine).  Whilst one could still do this, it seems unideal for someone who is not technically inclined, and is just kind of a pain.  

So, this created the need for this little project!  It's basically a mini version of the NFS drive feature of the New CIF Panel, allowing admins to log in, upload, and remove minutes from that local directory, from anywhere on the University Network.  Pretty cool, if I do say so myself.  : )

## Methodology, and setup. 

Due to some quirks of our network, the DMZ doesn't have direct access to much on the 220 (our standard vlan), which prevents users authenticating via LDAP, which in turn led to some creative solutions.  Namely, the program ssh-s into another server, which has access to those ports, to kinit, and check if the user is a member of the admins group.  If that script succeeds, the user is an admin, and are allowed to log in.  This script lies under `CHECKING_SERVER/check_admin.sh`

This requires an SSH key, which you can create using the usual method, provided that a service account has been created on that secondary server.  I'd recommend creating a random password for this user.  Note that the private SSH key you create should go into the `PRIVATE` directory.  Put the script in `CHECKING_SERVER` directory (`CHECKING_SERVER/check_admin.sh`) into that created user's home directory.  

From there, all you should need do is make an `app.cfg` file (Based on `app_example.cfg`), configuring things properly, and edit `scripts/check_admin.sh` to make sure everything there is correct based on your setup.  

Remember to create a python virtual environment, and install flask.  It should be the only thing you need to install via pip.  

## Closing remarks

'Tis been fun.  : )

Hopefully, you all keep the minutes on the website up-to-date with this new and fun utility!  As dull as it may be, information good.  Please make sure it it up to date frequently, and upload minutes frequently.  



