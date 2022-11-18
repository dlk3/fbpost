# Automate Facebook Profile Posts

I want WordPress to make a post to my Facebook profile when I publish a new WordPress post. All the WordPress plugins for Facebook use the official Facebook API which only supports posting to a Facebook page. I didn't want that. I want my posts to go into my profile/timeline. I've written a hack that does what I want by using an application user interface testing tool to drive a live browser session on my workstation to make a Facebook profile post whenever I publish a new WordPress post.

Florian Domgjoni pointed the way on [Python In Plain English](https://python.plainenglish.io/automating-facebook-posts-with-python-using-selenium-7a7ffca0f325).  There he described using the [Python Selenium UI test automation tool](https://selenium-python.readthedocs.io/) to automate a browser session to make Facebook posts.  Thanks Florian!

I took Florian's script and turned it into a [Python Flask](https://flask.palletsprojects.com/en/2.2.x/) web service that runs in the background in my user session on my desktop workstation. I installed a webhooks plugin in my WordPress instance out on the internet that sends a message to that desktop web service each time I publish a new WordPress post. It then makes a corresponding post to my Facebook profile.  Now it does what I want.

Important things to notice:
* Every time this web service makes a Facebook post it is going to open up a browser window on the desktop and drive the posting process in that session to make the post.  You'll see this happen right in front of you, right after you've clicked the publish button in WordPress.
* This web service runs on my local workstation, on my home intranet, behind my firewall.  Port forwarding must be configured through the firewall to allow the service to receive the requests coming from the WordPress webhooks plugin out on the public internet.  
  * If you're going to be doing this from a mobile laptop then there will be additional challenges.  IP addresses will be changing as you move around, firewalls between the laptop and the internet will come and go, etc.  You'll have to figure out a mechanism to maintain the link between the WordPress webhooks plugin and the service running on the laptop.  The potential solutions are as varied as the different network configurations will be.
* In this script Selenium uses the Firefox browser.  I did this to avoid conflicts.  Firefox is my secondary browser, I have it installed but I hardly ever use it.  Google Chrome is my default browser.  Whatever your situation is, Selenium also [supports Chrome, Edge and Safari](https://selenium-python.readthedocs.io/installation.html#drivers).  You can pick the option that works for you and tweak the script accoringly.

## My Setup

### On The Desktop

Fedora doesn't provide a package for the Selenium Python modules, they have to be installed using pip.  It's my habit to set up a Python virtual environment whenever this sort of thing is necessary.  It prevents whatever application-specific stuff  I'm doing from polluting my desktop Python environment.

Clone the fbpost repo from GitHub:
<pre>
$ cd ~/src
$ git clone https://github.com/dlk3/fbpost.git
$ cd fbpost
</pre>

Create Python virtual environment and install dependencies:
<pre>
$ python -m venv ~/src/fbpost
$ source ./bin/activate
$ pip install --upgrade pip
$ pip install selenium  geckodriver-autoinstaller flask gunicorn
</pre>

Open firewall port for the service (use your own personal zone name and port number):
<pre>
$ sudo firewall-cmd --zone=zonename --add-port 8888/tcp --permanent
$ sudo firewall-cmd --reload
</pre>

Create <code>fbpost.cfg</code> file using <code>fbpost.cfg.sample</code> as a template.  Note that the "urlstartswith" setting in that file is an important security feature.  It should be set to the URL of your blog, which will be the base of any permalinks sent from the WordPress webhook.  If other people send requests to this service with other URLs in them, the service will assume these are hacking attempts and ignore them.

To run the service in the foreground, for testing (use your desktop's IP address on your local LAN, 0.0.0.0 is not valid, and your own target port number):
<pre>
$ source bin/activate
(fbpost) $ gunicorn --bind=0.0.0.0:8888 fbpost:app
[2022-11-18 17:34:18 -0500] [1739250] [INFO] Starting gunicorn 20.1.0
[2022-11-18 17:34:18 -0500] [1739250] [INFO] Listening at: http://0.0.0.0:8888 (1739250)
[2022-11-18 17:34:18 -0500] [1739250] [INFO] Using worker: sync
[2022-11-18 17:34:18 -0500] [1739251] [INFO] Booting worker with pid: 1739251
Ctrl-C to terminate
$ deactivate
</pre>

#### To start the service automagically in the background when you login

Copy the <code>fbpost.service</code> file into your <code>~/.local/share/systemd/user/</code> directory and enable the service:
<pre>
$ mkdir -p ~/.local/share/systemd/user
$ cp fbpost.service ~/.local/share/systemd/user/
$ systemctl --user daemon-reload
$ systemctl --user enable fbpost
</pre>

### On The Internet Firewall/Router

Set up port forwarding from whatever externally-facing internet port you want to use and the port exposed by the Python Flask fbpost web service running on your desktop.

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

### That's It

Now, when you publish a new WordPress post, the webhook plugin will send a request to the service on your desktop, which will open up the browser and make a Facebook post announcing the new WordPress post to all your followers..
