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

long previousPotPos = 0;
long previousPotMoveTime = 0;
long stateChangeTime = 0;
long stateChangePot = 0;
long previousPotPosDiff = 0;
long iterations_in_state = 0;

#define  POT_POS_TOLERANCE 10
#define MAX_TIME_IN_BACK_TO_FOLLOW_MODE (1000*5)


#define motorPin1  2
#define motorPin2  3
#define motorPin3  4
#define motorPin4  5

AccelStepper stepper(8, motorPin1, motorPin3, motorPin2, motorPin4);

// STATE OF THE MOTOR FOLLOWING SYSTEM
#define STATE_0_OFF             0
#define STATE_1_BEGINNING       1
#define STATE_2_FOLLOWING       2
#define STATE_3_RECENTLY_MOVED  3
#define STATE_4_BACK_TO_FOLLOW  4
#define STATE_5_END             5


byte state = STATE_0_OFF;
byte statePrev = STATE_0_OFF;


bool debug = 1;
bool debug_state = 1;


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

#define DEBUG_STATE_PRINT_LINE() do { if (debug_state)Serial.println( String("St ") + __LINE__); }while(0);

void interrupt_periodic_stepper(void) {
  stepper.run();
  if ( stepper.isRunning() ) stepper.enableOutputs();
  else stepper.disableOutputs();
}

#define AVA_CAR_POT_MOVE_DELAY (1000*4)
#define POT_START  55
#define POT_END    1000

#define POT_TO_STEPS (-3)


void setAvaCarPos(float percentage)
{
  int   potPos             = analogRead(ANALOG_IN);
  float  avaCarPotGoal      = POT_START + (POT_END - POT_START) * percentage;
  float  potPosDiff         = avaCarPotGoal - potPos;
  float  potPosDiffAbs         = abs(potPosDiff);
  long   stepperPosNow      = stepper.currentPosition();
  float  nextStepperGoal    = stepperPosNow + (potPosDiff * POT_TO_STEPS );

  if ( percentage > 1.0 ) {
    state = STATE_5_END;
    DEBUG_STATE_PRINT_LINE()
    percentage = 1.0;
  }
  if ( percentage < 0.0 ) {
    state = STATE_5_END;
    DEBUG_STATE_PRINT_LINE()
    percentage = 0.0;
  }

  if ( potPosDiffAbs < POT_POS_TOLERANCE ) {
    state = STATE_2_FOLLOWING;
    //DEBUG_STATE_PRINT_LINE()
  } else
  {
    if ( (state == STATE_2_FOLLOWING) || (state == STATE_5_END) )
    {
      state = STATE_3_RECENTLY_MOVED ;
      DEBUG_STATE_PRINT_LINE()

      previousPotMoveTime = millis();
    }
    if ( state == STATE_3_RECENTLY_MOVED )
    {
      int pot_prev_abs_diff = potPos - stateChangePot;

      if ( pot_prev_abs_diff < 0)
      {
        pot_prev_abs_diff = -pot_prev_abs_diff;
      }
      if ( pot_prev_abs_diff > 3) {

        stateChangeTime = millis();
        stateChangePot = potPos;
      }
      else {
        long delay_since_last_move = millis() - stateChangeTime;
        if ( delay_since_last_move > AVA_CAR_POT_MOVE_DELAY )
        {
          state = STATE_4_BACK_TO_FOLLOW;
          previousPotPosDiff = potPosDiff;
          stateChangeTime = millis();
          stateChangePot = potPos;
          iterations_in_state = 0;
          DEBUG_STATE_PRINT_LINE()
        }
      }
    }
    if ( state == STATE_4_BACK_TO_FOLLOW )
    {
      long delay_since_state_transition = millis() - stateChangeTime;
      if ( delay_since_state_transition > MAX_TIME_IN_BACK_TO_FOLLOW_MODE ) {
        state = STATE_3_RECENTLY_MOVED ;
        DEBUG_STATE_PRINT_LINE()

        previousPotMoveTime = millis();
      }

      //mikael previousPotMoveTime


      long abs_diff_CurrentPotDiff_PreviousPotDiff =  previousPotPosDiff - potPosDiff;
      if ( previousPotPosDiff < 0) {
        abs_diff_CurrentPotDiff_PreviousPotDiff = - abs_diff_CurrentPotDiff_PreviousPotDiff;
      }

      if ( abs_diff_CurrentPotDiff_PreviousPotDiff > 3) {
        Serial.println( String("Moved ") + abs_diff_CurrentPotDiff_PreviousPotDiff);
        state = STATE_3_RECENTLY_MOVED ;
        DEBUG_STATE_PRINT_LINE()
      }
      previousPotMoveTime = millis();
    }
  }


  if ( (state == STATE_1_BEGINNING) ||  (state == STATE_2_FOLLOWING) ||  (state == STATE_4_BACK_TO_FOLLOW) )
  {
    stepper.moveTo(nextStepperGoal);
    if (debug) Serial.println(String("S ") + state + " Goal " + avaCarPotGoal + " Pot " + potPos + " Stepper " + stepperPosNow + " Next " + nextStepperGoal   );
  }

  previousPotPos = potPos;
  previousPotPosDiff = potPosDiff;

  iterations_in_state++;
  if ( state != statePrev)
  {
    statePrev = state;
    stateChangeTime = millis();
    stateChangePot = potPos;
    iterations_in_state = 0;
  }



}

#define TRIP_PERCENTAGE_START 0.0
#define TRIP_PERCENTAGE_END   1.0
#define TRIP_SECONDS          (60*2)

/*

  // STATE OF THE MOTOR FOLLOWING SYSTEM
  #define STATE_0_OFF             0
  #define STATE_1_BEGINNING       1
  #define STATE_2_FOLLOWING       2
  #define STATE_3_RECENTLY_MOVED  3
  #define STATE_4_END             4


  byte state = STATE_0_OFF;
*/

void runCar( bool direction, long seconds)
{
  long time_millis_start = millis();
  long time_millis_end = time_millis_start + (seconds * 1000);
  float time_millis_duration = (seconds * 1000.0);
  state = STATE_1_BEGINNING;
  while (1) {
    long time_millis_now = millis();


    float position_percent = (time_millis_now - time_millis_start) / time_millis_duration;
    if (direction ) setAvaCarPos(position_percent);
    else            setAvaCarPos(1.0 - position_percent);
    if ( position_percent > (1.0 + 0.1) ) break;
  }
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

  if (0) {
    runBetween(55, 1000, (long)10 * 60 * 1000);
    //Serial.println("Bytt retning");
    delay(1000);
    runBetween(1000, 55, 3 * 1000);
    delay(1000);
  }

  runCar( 0, 30);
  delay(1000 * 5);

  runCar( 1, 30);

  //stepper.setSpeed(100);
}
