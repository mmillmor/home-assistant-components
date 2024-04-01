"""Config flow for Heatmiser NetMonitor integration."""
from __future__ import annotations

import logging
import time
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth

from homeassistant.components.climate.const import (
    HVACAction,
    HVACMode
)
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class HeatmiserStat:
    """Utility class for Heatmiser NetMonitor stats."""

    def __init__(
        self,
        id,
        name,
        current_temperature,
        target_temperature,
        hvac_mode,
        current_state,
        hw_timer_output,
        hw_boost_time,
    ):
        """Initialize the stat."""
        self.id = id
        self.name = name
        self.current_temperature = current_temperature
        self.target_temperature = target_temperature
        self.hvac_mode = hvac_mode
        self.current_state = current_state
        self.hw_timer_output=hw_timer_output
        self.hw_boost_time=hw_boost_time


class HeatmiserHub:
    """Heatmiser Hub controller."""

    def __init__(
        self, host: str, username: str, password: str, hass: HomeAssistant
    ) -> None:
        """Initialize the hub controller."""
        self.host = host
        self.username = username
        self.password = password
        self.hass = hass

    def async_auth(self) -> bool:
        """Validate the username, password and host."""

        response = requests.get(
            "http://" + self.host + "/quickview.htm",
            auth=HTTPBasicAuth(self.username, self.password),
        )
        if response.status_code == 200:
            return True
        else:
            return False

    async def authenticate(self) -> bool:
        """Validate the username, password and host asynchronously."""
        response = self.hass.async_add_executor_job(self.async_auth)

        return response

    def set_time(self):
        """Get the networkSetup."""

        response = requests.get(
            "http://" + self.host + "/networkSetup.htm",
            auth=HTTPBasicAuth(self.username, self.password),
        )

        if response.status_code == 200:
            content = response.content.decode("utf-8")
            formValues = content.split('input type=hidden name="')
            ip=formValues[4].split('"')[2]
            mask=formValues[5].split('"')[2]
            gate=formValues[6].split('"')[2]
            dns=formValues[7].split('"')[2]
            gmtflag=formValues[11].split('"')[2]
            pin=formValues[12].split('"')[2]
            localTime=datetime.now()
            timeStr=localTime.strftime("%H:%M")
            dateStr=localTime.strftime("%d/%m/%Y")
            postData={"rdbkck": 0
		    ,"lognm":self.username
		    ,"logpd":self.password
		    ,"ip":ip
		    ,"mask":mask
		    ,"gate":gate
		    ,"dns":dns
		    ,"timestr":timeStr
		    ,"datestr":dateStr
		    ,"timeflag":1
		    ,"gmtflag":1
		    ,"pin":pin}

            response = requests.post(
		    "http://" + self.host + "/networkSetup.htm",
		    data=postData,
		    auth=HTTPBasicAuth(self.username, self.password),
            )
    
    async def set_time_async(self):
        """Set the time asynchronously."""
        return await self.hass.async_add_executor_job(self.set_time)

    def set_boost(self, name, hours):
        """Set a hot water boost time."""

        for _ in range(10):
            response = requests.post(
                "http://" + self.host + "/right.htm",
                data={"rdbkck": "1", "curSelStat": name},
                auth=HTTPBasicAuth(self.username, self.password),
            )
            if response.status_code == 200:
                response = requests.post(
                    "http://" + self.host + "/right.htm",
                    data={"hwBoost": '{0:02d}'.format(int(hours))},
                    auth=HTTPBasicAuth(self.username, self.password),
                )
            time.sleep(1)
    
    async def set_boost_async(self,name,hours):
        """Set the time asynchronously."""
        return await self.hass.async_add_executor_job(self.set_boost,name,hours)


    def get_devices(self):
        """Get the list of devices."""

        device_list = []
        response = requests.get(
            "http://" + self.host + "/quickview.htm",
            auth=HTTPBasicAuth(self.username, self.password),
        )
        if response.status_code == 200:
            content = response.content.decode("utf-8")
            statnames = content.split('statname" value="')[1].split('"')[0].split("#")
            quickvals = content.split('quickview" value="')[1].split('"')[0]
            statmap = content.split('statmap" value="')[1].split('"')[0]
            i = 0
            for statname in statnames:
                if (statmap[i : i + 1]) == "1":
                    current_temperature_str = quickvals[i * 6 : i * 6 + 2]
                    current_temperature = None
                    if current_temperature_str != "NC":
                        current_temperature = int(current_temperature_str)
                    target_temperature_str = quickvals[i * 6 + 2 : i * 6 + 4]
                    target_temperature = None
                    if target_temperature_str != "NC":
                        target_temperature = int(target_temperature_str)
                    state = quickvals[i * 6 + 4 : i * 6 + 5]
                    current_state = HVACAction.OFF
                    if state == "1":
                        current_state = HVACAction.HEATING
                    hw_state = quickvals[i * 6 + 5 : i * 6 + 6]
                    hw_timer_output = STATE_UNAVAILABLE
                    if hw_state == "0":
                        hw_timer_output = STATE_OFF
                    elif hw_state == "1":
                        hw_timer_output = STATE_ON

                    print(
                        statname
                        + "("
                        + current_temperature_str
                        + " "
                        + target_temperature_str
                        + ")"
                    )

                    device_list.append(
                        HeatmiserStat(
                            i,
                            statname,
                            current_temperature,
                            target_temperature,
                            HVACMode.HEAT,
                            current_state,
                            hw_timer_output,
                            -1
                        )
                    )
                    i = i + 1
        return device_list

    async def get_devices_async(self):
        """Get the list of devices asynchronously."""
        return await self.hass.async_add_executor_job(self.get_devices)

    def set_temperature(self, name, target_temperature):
        """Set a device target temperature."""

        for _ in range(10):
            response = requests.post(
                "http://" + self.host + "/right.htm",
                data={"rdbkck": "1", "curSelStat": name},
                auth=HTTPBasicAuth(self.username, self.password),
            )
            if response.status_code == 200:
                response = requests.post(
                    "http://" + self.host + "/right.htm",
                    data={"selSetTemp": str(int(target_temperature))},
                    auth=HTTPBasicAuth(self.username, self.password),
                )
            time.sleep(1)

    async def set_temperature_async(self, name, target_temperature):
        """Set a device target temperature asynchronously."""
        return await self.hass.async_add_executor_job(
            self.set_temperature, name, target_temperature
        )

    def set_mode(self, name, hvac_mode):
        """Set a device target mode."""
        mode = "0"
        if hvac_mode == HVACMode.OFF:
            mode = "1"
        for _ in range(10):
            response = requests.post(
                "http://" + self.host + "/right.htm",
                data={"rdbkck": "1", "curSelStat": name},
                auth=HTTPBasicAuth(self.username, self.password),
            )
            if response.status_code == 200:
                response = requests.post(
                    "http://" + self.host + "/right.htm",
                    data={"selFrost": mode},
                    auth=HTTPBasicAuth(self.username, self.password),
                )
            time.sleep(1)

    async def set_mode_async(self, name, hvac_mode):
        """Set a device target mode asynchronously."""
        return await self.hass.async_add_executor_job(self.set_mode, name, hvac_mode)

    def get_device_status(self, name) -> HeatmiserStat:
        """Get the device status."""

        response = requests.post(
            "http://" + self.host + "/right.htm",
            data={"rdbkck": "0", "curSelStat": name},
            auth=HTTPBasicAuth(self.username, self.password),
        )
        if response.status_code == 200:
            content = response.content.decode("utf-8")
            statvals = content.split('statInfo" value="')[1].split('"')[0]
            current_temperature_str = statvals[0:2]
            current_temperature = None
            if current_temperature_str != "NC":
                current_temperature = int(current_temperature_str)
            target_temperature_str = statvals[2:4]
            target_temperature = None
            if target_temperature_str != "NC":
                target_temperature = int(target_temperature_str)
            current_state = statvals[8:9]
            current_mode = statvals[10:11]
            mode = HVACMode.HEAT
            if current_mode == "1":
                mode = HVACMode.OFF
                state = HVACAction.OFF
            else:
                state = HVACAction.IDLE
                if current_state == "1":
                    state = HVACAction.HEATING
                
            hw_timer_output=STATE_UNAVAILABLE
            try:
                current_hw_available = int(statvals[12:13])
                if current_hw_available >2:
                    current_hw_state = statvals[11:12]
                    hw_timer_output=STATE_OFF
                    if current_hw_state =="1":
                        hw_timer_output=STATE_ON
            except(ValueError, TypeError):
                pass

            boostTime=-1
            boostVals = content.split('hwBoost" value="')[1].split('"')[0]
            if boostVals !="ff":
                boostTime=int(boostVals)

            stat = HeatmiserStat(
                0, name, current_temperature, target_temperature, mode, state,hw_timer_output,boostTime
            )
            return stat
        else:
            return None

    async def get_device_status_async(self, name) -> HeatmiserStat:
        """Get the device status asynchronously."""
        return await self.hass.async_add_executor_job(self.get_device_status, name)
