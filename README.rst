*************
humantrafficking.tips
*************

A bot for receiving human trafficking tips via SMS and distributing to response units via email.

Powered by `Django`_ and `Twilio`_. Built at the `End Human Trafficking hackathon`_ in October 2016.


**Table of Contents**


.. contents::
    :local:
    :depth: 1
    :backlinks: none


Installation
===========

Install this `Django`_ application by first cloning the repository.

.. code-block:: bash
  
    git clone https://github.com/RobSpectre/humantrafficking.tips


Create a local configuration file and customize with your settings.

.. code-block:: bash
   
    cd humantrafficking.tips/humantrafficking_tips/humantrafficking_tips
    cp local.sample local.py


Create database.

.. code-block:: bash

    cd ..
    python manage.py makemigrations
    python manage.py migrate

Run the server

.. code-block:: bash

    python manage.py runserver

Configure a `Twilio phone number`_ to point to the `/sms` endpoint of your host.

.. image:: https://raw.githubusercontent.com/RobSpectre/humantrafficking.tips/master/humantrafficking_tips/humantrafficking_tips/static/images/twilio_phone_number_screenshot.png 
    :target: https://www.twilio.com/console/phone-numbers/incoming

Text "HELP" to the number you configured.
 


Meta
============

* Written by `Rob Spectre`_
* Released under `MIT License`_
* Software is as is - no warranty expressed or implied.


.. _Rob Spectre: http://www.brooklynhacker.com
.. _MIT License: http://opensource.org/licenses/MIT
.. _Django: https://www.djangoproject.com/
.. _Twilio: https://twilio.com
.. _Twilio phone number: https://www.twilio.com/console/phone-numbers/incoming
.. _End Human Trafficking hackathon: https://ehthackathon.splashthat.com/
