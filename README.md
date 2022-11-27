# Automate Facebook Profile Posts

I want WordPress to make a post to my Facebook profile when I publish a new WordPress post. All the WordPress plugins for Facebook use the official Facebook API which only supports posting to a Facebook page. I didn't want that. I want my posts to go into my profile/timeline. I've written a hack that does what I want by using an application user interface testing tool to drive a live browser session on my workstation to make a Facebook profile post whenever I publish a new WordPress post.

Florian Domgjoni pointed the way on [Python In Plain English](https://python.plainenglish.io/automating-facebook-posts-with-python-using-selenium-7a7ffca0f325).  There he described using the [Python Selenium UI test automation tool](https://selenium-python.readthedocs.io/) to automate a browser session to make Facebook posts.  Thanks Florian!

I took Florian's script and turned it into a systemd.socket-driven web service that runs in my user session on my desktop workstation. I installed a webhooks plugin in my WordPress instance out on the internet that sends a message to that desktop web service each time I publish a new WordPress post. It then makes a corresponding post to my Facebook profile.  Now it does what I want.

Important things to notice:
* Every time this web service makes a Facebook post it is going to open up a browser window on the desktop and drive the posting process in that session to make the post.  You'll see this happen right in front of you, right after you've clicked the publish button in WordPress.  The publishing proces in WordPress will pause and wait until the posting process is complete before it completes.
* This web service runs on my local workstation, on my home intranet, behind my firewall.  Port forwarding must be configured through the firewall to allow the service to receive the requests coming from the WordPress webhooks plugin out on the public internet.  
* If you're going to be doing this from a mobile laptop then there will be additional challenges.  IP addresses will be changing as you move around, firewalls between the laptop and the internet will come and go, etc.  You'll have to figure out a mechanism to maintain the link between the WordPress webhooks plugin and the service running on the laptop.  The potential solutions are as varied as the different network configurations will be.
* In this script Selenium uses the Firefox browser.  I did this to avoid conflicts.  Firefox is my secondary browser, I have it installed but I hardly ever use it.  Google Chrome is my default browser.  Whatever your situation is, Selenium [supports Firefox, Chrome, Edge and Safari](https://selenium-python.readthedocs.io/installation.html#drivers).  You can pick the option that works best for you and tweak the script to load the appropriate browser driver.
* Whatever browser is used, it is important to log in manually to the https://m.facebook.com site at least once using that browser so that cookies and user validation are done before trying to use this service.  The service is not designed to handle those complexities.

## Setup

### On The Desktop

Clone the fbpost repo from GitHub:
<pre>
$ cd ~/src
$ git clone https://github.com/dlk3/fbpost.git
$ cd fbpost
</pre>

Move the fbpost script file into place:
<pre>
$ sudo cp fbpost /usr/local/bin/fbpost
</pre>

Install the Python Selenium module dependencies:
<pre>
$ sudo dnf install python3-selenium
$ pip install geckodriver-autoinstaller
</pre>

Set the userid and the port number in the <code>fbpost.socket</code> and <code>fbpost.service</fbpost> files.  The <code>User=</code> option in each of these files should be set to your normal login id.  We want the browser that does the Facebook posting to run as you, not root. The port number set in the <code>fbpost.socket</code> file only needs to be changed if you want to use a local port that's different than the one I picked, 8081.  Note that this is not the port that will be exposed to the internet and to WordPress.  That will be determined by how port forwarding is configured in your internet router.  This is the port the service exposes on your local LAN.
 
Open the local host's firewall to allow traffic on the service port:
<pre>
$ sudo firewall-cmd --add-port 8081/tcp --permanent
$ sudo firewall-cmd --reload
</pre>
(In my case I have to add the <code>--zone=libvirt</code> option to the command line to open this port on the correct network interface.)

Create the <code>/etc/sysconfig/fbpost.conf</code> file using <code>fbpost.conf.template</code> as a template.  This file must be customized properly for this service to function.  See the comments in the file for guidance.

Move the systemd files into place, enable and start the systemd socket listener:
<pre>
$ sudo cp fbpost.socket /etc/systemd/system/
$ sudo cp fbpost.service /etc/systemd/system/
$ sudo systemctl daemon-reload
$ sudo systemctl enable fbpost.socket
$ sudo systemctl start fbpost.socket
</pre>

Informational and error messages from the service are written into syslog.  Control the log level by changing the "level=logging.INFO" setting near the top of the "fbpost" script file.  See the [Python documentation](https://docs.python.org/3/library/logging.html#logging-levels) for valid level options.

### On The Internet Firewall/Router

Set up port forwarding from whatever externally-facing internet port you want to the port specified in the fbpost.socket file.

### In WordPress

1.  Install the [WP Webhooks](https://wordpress.org/plugins/wp-webhooks/) plugin.
2.  Add a "Post created" webhook that points to the externally-facing internet port you defined on your firewall/router: <code>http://hostname:port/</code>
3.  Click the three-dot icon next to the webhook and select "Settings:"
    <br />Trigger on selected post types: Post
    <br />Trigger on initial post status change: Published
    <br />Allow unsafe URLs: On
    <br />Allow unverified SSL: On
4. Click "Save Settings"

Notice the "Send Demo" option on the three-dot menu, it will send a sample webhook request to the target URL to help with testing.

### Testing / Posting Manually

The web service can be manually invoked locally on the system on which it is installed by doing something like this (substituting your own permalink):
<pre> 
$ curl -X POST --header "Content-Type: application/json" -d '{"post_permalink":"https://whatever"}' localhost:8081</code>
</pre>

Monitor the syslog on the local host to see any progress or error messages.  (<code>journalctl -e</code> or <code>journalctl -f</code>)

### That's It

Now, when you publish a new WordPress post, the webhook plugin will send a request to the service on your desktop, which will open up the browser and make a Facebook post announcing the new WordPress post to all your friends and followers.
