// ProportionalControl.pde
// -*- mode: C++ -*-
//
// Make a single stepper follow the analog value read from a pot or whatever
// The stepper will move at a constant speed to each newly set posiiton,
// depending on the value of the pot.
//
// Copyright (C) 2012 Mike McCauley
// $Id: ProportionalControl.pde,v 1.1 2011/01/05 01:51:01 mikem Exp mikem $
#include <AccelStepper.h>
#include <TimerOne.h>

// Define a stepper and the pins it will use

#define motorPin1  2
#define motorPin2  3
#define motorPin3  4
#define motorPin4  5

AccelStepper stepper(8, motorPin1, motorPin3, motorPin2, motorPin4);

// This defines the analog input pin for reading the control voltage
// Tested with a 10k linear pot between 5v and GND
#define ANALOG_IN A0

int analog_in;
long moveSpeed = -2;
void setup()
{
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(2000);
  Serial.begin(115200);

  Timer1.initialize(100); // Period: 100uSec == 10.000 Hz Interrupts
  Timer1.attachInterrupt(interrupt_periodic_stepper);
  delay(5000);

}

bool debug=0;


void interrupt_periodic_stepper(void) {
  stepper.run();
  if ( stepper.isRunning() ) stepper.enableOutputs();
  else stepper.disableOutputs();
}

void runBetween(long startPos, long endPos, long duration) {

  long startTime = millis();
  long endTime = startTime + duration;
  long lengthMove = endPos - startPos;
  bool moveDir = (startPos > endPos);


  while (1) {
    long current_pos = analogRead(ANALOG_IN);
    long current_time = millis();

    float current_relative_time = current_time - startTime;
    
    current_relative_time /= duration;


    //if ( current_relative_time > duration) break;



    long relative_pos_desired = startPos + (lengthMove * current_relative_time);
    if (debug) Serial.print("Goal_pot " );

    if (debug) Serial.print(relative_pos_desired);

    // Time for serial
    //Serial.print("t");
    Serial.print(relative_pos_desired);

    
    long relative_stepper_move = (relative_pos_desired - current_pos) * moveSpeed;
    long new_stepper_pos = stepper.currentPosition() + relative_stepper_move;

    /*
    if( abs( current_pos - relative_pos_desired ) > 20) {
      delay(5000);
      stepper.moveTo(stepper.currentPosition());
    }
    */

    // Position for serial
    Serial.print(",");
    Serial.println(current_pos);

    if (debug) Serial.print("   Pot_now " );

    if (debug) Serial.print(current_pos);
    if (moveDir)
    {
      if (current_pos < endPos ) {
         stepper.moveTo(stepper.currentPosition());
        if (debug) Serial.println();
        if (debug) Serial.println("Break1");
        break;
      }
    }

    else if (current_pos > endPos ) {
      stepper.moveTo(stepper.currentPosition());
      if (debug) Serial.println();
      if (debug) Serial.println("Break2");
      break;
    }
if (debug) {
    Serial.print("  St_now " );

    Serial.print(stepper.currentPosition());

    Serial.print("  St_new " );

    Serial.print(new_stepper_pos);

    Serial.print("  Diff " );

    Serial.println(relative_stepper_move);
}
    //stepper.move(-relative_stepper_move);
    stepper.moveTo(new_stepper_pos);

    delay(100);

  }
  Serial.println();
  Serial.println("Ended the while loop" );

}
void loop()
{
  // Read new position
  //analog_in = analogRead(ANALOG_IN);
  //Serial.println(analog_in);
  //stepper.moveTo((analog_in*4)-2000);
  //delay(100);

  runBetween(55, 1000, (long)10 * 60 * 1000);

  //Serial.println("Bytt retning");
  delay(1000);
  runBetween(1000, 55, 3 * 1000);

  delay(1000);


  //stepper.setSpeed(100);
}
