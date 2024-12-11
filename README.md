# Home Assistant Components

I have a few home assistant components that I've built/adapted which you are welcome to use

## Gecko

This is based on https://github.com/gazoodle/gecko-home-assistant by @gazoodle, optimised for the inYT plateform spas


## Heatmiser Netmonitor

Integration with Heatmier Netmonitor systems. This integration offers thermostat and hot water control. It also has two services;

1. Hot water boost - this will boost the hot water for the specified time
2. Set time - this will set the system time to the current time. Note, you must call this for one entity, but it will update the whole system when you do

## Service examples

### Set away when you leave a zone

To set the system to Away status when you leave a zone, create an automation of type "Create new automation", with a trigger of Time and location -> Zone, and an action of Heatmiser NetMonitor 'Set Away'

![image](https://github.com/user-attachments/assets/7400c425-bf6d-46e3-8a1b-77dc1097142f)

The yaml for this looks like;

```
description: ""
mode: single
triggers:
  - trigger: zone
    entity_id: device_tracker.pixel_7_2
    zone: zone.home
    event: leave
conditions: []
actions:
  - action: heatmiser_netmonitor.set_away
    metadata: {}
    data: {}
    target:
      entity_id: climate.bedroom
```

### Set Away when you press a button

To add a toggle to the home page which switches between home and away, first of all add a Helper toggle under Devices -> Helpers

![image](https://github.com/user-attachments/assets/4c4eee00-4306-415c-9fb7-130bf2d9a990)

Next, add an automation based on the toggle state, which is called whenever the state changes. Add a conditional action which sets the state to Home if on, and Away if off 

![image](https://github.com/user-attachments/assets/8ee67ceb-cba0-4b99-aa68-fdac4771dc09)

the yaml for this looks like;

```
alias: Heating Home/Away
description: ""
triggers:
  - trigger: state
    entity_id:
      - input_boolean.home_away
conditions: []
actions:
  - choose:
      - conditions:
          - condition: state
            entity_id: input_boolean.home_away
            state: "on"
        sequence:
          - action: heatmiser_netmonitor.set_home
            metadata: {}
            data: {}
            target:
              entity_id: climate.bedroom
      - conditions:
          - condition: state
            entity_id: input_boolean.home_away
            state: "off"
        sequence:
          - action: heatmiser_netmonitor.set_away
            metadata: {}
            data: {}
            target:
              entity_id: climate.bedroom
mode: single
```


