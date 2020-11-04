/*
   This uses the primary examples from the author of NewPing to drive sonic sensor.
   It only outputs the microsecond data to the serial monitor, but the calculation for
   distance has been left in and commented out.
   For logging to a computer this sketch is used with the python module arduino_streaming.py
   to dump data to csv file.
*/

/*
  Arduino/sensor set up
  Some of the code is from 
  DroneBot Workshop 2017
  https://dronebotworkshop.com/hc-sr04-ultrasonic-distance-sensor-arduino/#1
*/

// Microsecond echo response time data can be displayed on the Serial Monitor
//to display Range Finder distance readings, but the data is also on the usb port.

// Include NewPing Library for HC-SR04 Ultrasonic Range Finder
#include <NewPing.h>

// Hook up HC-SR04 as indicated here, or change Pin Assignments
//    TRIG to Arduino Pin 4, 
//    Echo to Arduino pin 5
//    Maximum Distance is 550 cm (4m)

#define TRIGGER_PIN  4
#define ECHO_PIN     5
#define MAX_DISTANCE 550

//Initialize the sensor pin setup and distance
NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE);
unsigned int duration; //output will be in usec
//float distance; //uncomment if printing distance or combination duration and distance
const int iterations = 2000; // can't use much more than 500 if using for array.
//unsigned int pings[iterations];
int cnt = 0;
void setup() {
  Serial.begin (9600);
  for (cnt = 0; cnt <= iterations; cnt++) {
    duration = sonar.ping(); //single pings @delay time.
    //distance = (duration / 2) * 0.03445;
    Serial.println(duration);
    //To print duration,distance to serial monitor, comment out above 
    //and uncomment following:
    //DO NOT UNCOMMENT THE BELOW SECITON unless Arduino_serial.py modified
    //to accept both data.
    //Serial.print(duration);
    //Serial.print(",");  
    //Serial.println(distance);
    delay(33);
  }
  //declared duration as integer, so have to look for integer
  //this is used for manual ID only; problem with detection in python module
  Serial.println(111111);
}

//void loop returns nothing, but Arduino is still running, of course.
void loop() {
}
