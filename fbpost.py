#!/usr/bin/env python

import logging

#  Read external configuration file
config_file = 'fbpost.cfg'
try:
	import json
	with open(config_file) as cfgfile:
		cfg = json.load(cfgfile)
except:
	logging.exception('Unable to read {}'.format(config_file), exc_info=True)
	exit(1)

#  Import Flask
try:
	from flask import Flask
	from flask import request
	app = Flask(__name__)
except:
	logging.exception('There was a problem importing the Python Flask modules.  Are they installed?', exc_info=True)
	exit(1)

#  Import Python API for Selenium browser test automation
try:
	from selenium import webdriver
	from selenium.webdriver.support import expected_conditions as EC
	from selenium.webdriver.support.ui import WebDriverWait
	from selenium.webdriver.common.by import By
	import geckodriver_autoinstaller
except:
	logging.exception('There was a problem importing the Python modules for Selenium.  Are they installed? (pip install selenium geckodriver_autoinstaller)', exc_info=True)
	exit(1)

#  Write log output into a file
logging.basicConfig(filename=cfg['logfile'], encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

#  Do a Facebook post using Selenium browser automation when the default route is called
@app.route('/', methods=['POST'])
def fbpost():

	logging.debug('received a request')
	
	#  Get the request data and validate the permalink
	try:
		post = request.get_json()
		logging.debug(json.dumps(post, indent=4))
		if not post['post_permalink'].startswith(cfg['urlstartswith']):
			logging.error('Ignoring request, permalink does not validate: {}'.format(post['post_permalink']))
			return 'Invalid permalink in request data', 500
	except:
		logging.exception('Unable to get post data from HTTP request', exc_info=True)
		return 'Unable to get post data from HTTP request', 500
	
	#  Construct post message
	try:
		fb_post = 'New "Whatcha Doin\'?" blog post:\n{}\n'.format(post['post_permalink'])
	except:
		logging.exception('Unable to build message for posting', exc_info=True)
		return 'Unable to build message for posting', 500

	#  Initialize Selenium and open browser session
	try:
		geckodriver_autoinstaller.install() 
		driver = webdriver.Firefox()
		wait = WebDriverWait(driver, 10)
	except:
		logging.exception('Exception while initializing Selenium browser automation session', exc_info=True)
		return 'Exception while initializing Selenium browser automation session', 500
		
	#  Log into Facebook
	try:
		driver.get('https://m.facebook.com/')
		userid_input = driver.find_element(By.XPATH, '//*[@id="m_login_email"]')
		userid_input.send_keys(cfg['facebook']['userid'])
		password_input = driver.find_element(By.XPATH, '//*[@id="m_login_password"]')
		password_input.send_keys(cfg['facebook']['passwd'])
		login_btn = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/div/div[3]/form/div[5]/div[1]/button')
		login_btn.click()
		wait.until(EC.url_changes('https://m.facebook.com/'))
	except:
		logging.exception('There was a problem logging into Facebook', exc_info=True)
		driver.quit()
		return 'There was a problem logging into Facebook', 500

	#  Make the post
	try:
		driver.get('https://m.facebook.com/')
		whats_on_your_mind = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[4]/div/div[1]/div[3]/div/div/div[1]/div/div[2]/div')
		post_input = whats_on_your_mind.find_element(By.XPATH, '..')
		post_input.click()
		wait.until(EC.presence_of_element_located((By.ID, 'uniqid_1')))
		post_text_area = driver.find_element(By.XPATH, '//*[@id="uniqid_1"]')
		post_text_area.send_keys(fb_post)
		wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sharerAttachmentMedia')))
		post_btn = driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div/div[2]/div/div/div[5]/div[3]/div/div/button')
		post_btn.click()
		wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), 'Your post is now published.')]")))
		logging.info('Facebook post published successfully')
		driver.quit()
		return 'Facebook post published successfully', 200
	except:
		logging.exception('There was a problem sending the post text to Facebook', exc_info=True)
		driver.quit()
		return 'There was a problem sending the post text to Facebook', 500

if __name__ == '__main__':
	app.run()
