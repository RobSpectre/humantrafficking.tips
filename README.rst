*************
humantrafficking.tips
*************

A bot for receiving human trafficking tips via SMS and distributing to response units via email.

Powered by `Django`_ and `Twilio`_. Built at the `End Human Trafficking hackathon`_ in October 2016.


.. image:: https://travis-ci.org/RobSpectre/humantrafficking.tips.svg?branch=master
    :target: https://travis-ci.org/RobSpectre/humantrafficking.tips

.. image:: https://coveralls.io/repos/github/RobSpectre/humantrafficking.tips/badge.svg?branch=master
    :target: https://coveralls.io/github/RobSpectre/humantrafficking.tips?branch=master


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


Install the Python dependencies.

.. code-block:: bash

    cd humantrafficking.tips
    pip install -r requirements.txt


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


Development
===========

Hacking
-----------

Install `RabbitMQ`_, required for the Celery task queue. Instructions for
Ubuntu.

.. code-block:: bash

    $ sudo apt-get update
    $ sudo apt-get install rabbitmq-server


To hack on the project, fork the repo and then clone locally.

.. code-block:: bash

    $ git clone https://github.com/RobSpectre/humantrafficking.tips.git

Move to the project directory.

.. code-block:: bash

    $ cd humantrafficking.tips 

Install the Python dependencies (preferably in a virtualenv).

.. code-block:: bash

    $ pip install -r requirements.txt 

Then customize your local variables to configure your `Twilio`_, email and
admin accounts you want to receive tips.

.. code-block:: bash

    $ cp humantrafficking_tips/humantrafficking_tips/local.sample humantrafficking_tips/humantrafficking_tips/local.py
    $ vim humantrafficking_tips/humantrafficking_tips/local.py

Move to the Django project root.

.. code-block:: bash

    $ cd humantrafficking_tips

Start the Celery task queue.


.. code-block:: bash

    $ celery -A humantrafficking_tips worker -l info 


Start the Django app.

.. code-block:: bash

    $ python manage.py runserver 


Testing
------------

Use Tox for easily running the test suite.

.. code-block:: bash

    $ tox


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
.. _RabbitMQ: https://www.rabbitmq.com/download.html
