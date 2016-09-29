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

#define  POT_POS_TOLERANCE 15
#define MAX_TIME_IN_BACK_TO_FOLLOW_MODE (1000*10)
// A VALUE BETWEEN 500 AND 1900
#define MOTOR_SPEED 1400

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
#define STATE_X_NO_STATE        -1

#define TRAVEL_AWAY 1
#define TRAVEL_HOME 0

// This defines the analog input pin for reading the control voltage
// Tested with a 10k linear pot between 5v and GND
#define ANALOG_POT_IN A0

#define AVA_CAR_POT_MOVE_DELAY (1000*2) // Hvor lenge bilen står stille
#define POT_START  55
#define POT_END    1000
#define POT_TO_STEPS (-2)

#define TRIP_PERCENTAGE_START 0.0
#define TRIP_PERCENTAGE_END   1.0
#define TRIP_SECONDS          (60 * 10)  // Lengde på turen
#define GO_HOME_SECONDS       5 

char state = STATE_0_OFF;
char statePrev = STATE_0_OFF;

long iterations_in_state = 0;
long lastTransition_time = 0;//previousPotMoveTime
long lastTransition_potPos = 0; //previousPotPos
long lastTransition_potPosDiffAbs = 0; // previousPotPosDiff

bool debug = 0;
bool debug_state = 0;
bool debug_state_transition = 0;

#define DEBUG_STATE_PRINT_LINE(); do { if (debug_state)Serial.println( String("St ") + __LINE__); }while(0)


void interrupt_periodic_stepper(void) {
  stepper.run();
  if ( stepper.isRunning() ) stepper.enableOutputs();
  else stepper.disableOutputs();
}

void setAvaCarPos(float percentage)
{
  if ( percentage > TRIP_PERCENTAGE_END ) {
    percentage = TRIP_PERCENTAGE_END;
  }
  if ( percentage < TRIP_PERCENTAGE_START ) {
    DEBUG_STATE_PRINT_LINE();
    percentage = TRIP_PERCENTAGE_START;
  }
  char next_state = STATE_X_NO_STATE;
  int   potPos             = readPot();
  Serial.print(potPos);
  Serial.print(",");
  float  avaCarPotGoal      = POT_START + (POT_END - POT_START) * percentage;
  Serial.println((int) avaCarPotGoal);
  float  potPosDiff         = avaCarPotGoal - potPos;
  float  potPosDiffAbs         = abs(potPosDiff);
  long   stepperPosNow      = stepper.currentPosition();
  /*int limit_max = 6
  int step_diff = (potPosDiff * POT_TO_STEPS );
  int step_limiter;
  if (step_diff > 6) step_diff
  */
  float  nextStepperGoal    = stepperPosNow + (potPosDiff * POT_TO_STEPS );
  long time_now = millis();
  long prev_diff_time = time_now - lastTransition_time;
  long prev_abs_diff_potPos  =  abs(lastTransition_potPos - potPos);
  long prev_diff_potPosDiffAbs = lastTransition_potPosDiffAbs - potPosDiffAbs;


  switch (state ) {
    case  STATE_0_OFF:

    case STATE_1_BEGINNING:
      next_state = STATE_2_FOLLOWING;
      break;
    case STATE_2_FOLLOWING:
      if ( potPosDiffAbs > POT_POS_TOLERANCE ) {
        next_state = STATE_3_RECENTLY_MOVED;
      }
      if ( percentage >= TRIP_PERCENTAGE_END  || percentage <= TRIP_PERCENTAGE_START) {
        next_state = STATE_5_END;
      }
      break;
    case STATE_3_RECENTLY_MOVED:
      if ( prev_abs_diff_potPos > 3) {
        next_state = state;
        DEBUG_STATE_PRINT_LINE();
      }
      else {
       // Serial.println( String( "test1: ") + prev_diff_time + " " + AVA_CAR_POT_MOVE_DELAY);
        if ( prev_diff_time > AVA_CAR_POT_MOVE_DELAY )
        {
          next_state = STATE_4_BACK_TO_FOLLOW;
          DEBUG_STATE_PRINT_LINE();
        }
      }
      break;
    case STATE_4_BACK_TO_FOLLOW:
      //Serial.println(String("mik " ) + potPosDiffAbs + " " + prev_diff_potPosDiffAbs +  " " + prev_diff_time );
      if ( potPosDiffAbs < POT_POS_TOLERANCE ) {
        next_state = STATE_2_FOLLOWING;
      }
      if ( prev_diff_time > MAX_TIME_IN_BACK_TO_FOLLOW_MODE ) {
        next_state = STATE_3_RECENTLY_MOVED;
        DEBUG_STATE_PRINT_LINE();
      }
      if ( prev_diff_potPosDiffAbs > 5 ) {
        next_state = state;
        DEBUG_STATE_PRINT_LINE();
      }
      if ( (prev_diff_potPosDiffAbs < -30) && (prev_diff_time > 100) ) {
        next_state = STATE_3_RECENTLY_MOVED;
        DEBUG_STATE_PRINT_LINE();
      }
      break;
    case STATE_5_END:
      if ( percentage < TRIP_PERCENTAGE_END  && percentage > TRIP_PERCENTAGE_START) {
        next_state =  STATE_1_BEGINNING;
      }
      break;
    default:
      ;
  }

  iterations_in_state++;
  if ( next_state != STATE_X_NO_STATE )
  {
    if (debug_state_transition) Serial.println( String("S ") + (byte)state + " -> " + (byte)next_state + " " + iterations_in_state);
    if (next_state != state ) iterations_in_state = 0;
    state = next_state;
    lastTransition_time = millis();
    lastTransition_potPos = potPos;
    lastTransition_potPosDiffAbs = potPosDiffAbs;
  }
  if ( (state == STATE_2_FOLLOWING) ||  (state == STATE_4_BACK_TO_FOLLOW) )
  {
    stepper.moveTo(nextStepperGoal);
  }

  if (debug) Serial.println(String(" Goal ") + avaCarPotGoal + " Pot " + potPos + " Stepper " + stepperPosNow + " Next " + nextStepperGoal + String(" S ") + (byte) state  );
  delay(20);
}

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

void setup()
{
  stepper.setMaxSpeed(MOTOR_SPEED);
  stepper.setAcceleration(1800);
  Serial.begin(115200);

  Timer1.initialize(100); // Period: 100uSec == 10.000 Hz Interrupts
  Timer1.attachInterrupt(interrupt_periodic_stepper);
  delay(5000);

  int i = 0;
  while (1) {
    Serial.print(F("Nr trips left"));
    Serial.println(i);
    runCar( TRAVEL_AWAY, TRIP_SECONDS);
    delay(1000 * 5);
    runCar( TRAVEL_HOME, GO_HOME_SECONDS);
    delay(1000 * 5);
    i--;
  }
}

int readPot()
{
  int current = analogRead(ANALOG_POT_IN);
  static int prev1 = -1;
  static int prev2 = -1;
  static int prev3 = -1;
  if (-1==prev1 ) prev1 = current;
  if (-1==prev2 ) prev2 = current;
  if (-1==prev3 ) prev3 = current;
  int retval = (current+prev1+prev2+prev3)/4;
  prev3=prev2;
  prev2=prev1;
  prev1=current;
  return retval;
}

float get_percentage_from_pot() {
  int aval = readPot();
  float retval = (0.0 +aval - POT_START) / (POT_END - POT_START);
  return retval;
}

void travel_to(float destination)
{
  float current_pos = get_percentage_from_pot();
  float start_pos = current_pos;

  Serial.print("Going to: ");
  Serial.println(destination);
  Serial.print("Current pos:");
  Serial.println(current_pos);
  delay(1000);
  while ( current_pos <  destination)
  {
    current_pos += 1.0 / 20000;
    setAvaCarPos(current_pos);
  
  }
  while ( current_pos >  destination)
  {
    
    current_pos -= 1.0 / 20000;
    setAvaCarPos(current_pos);


 
  
  }
}

void loop()
{
  int input = 0;
  byte percent;
  float destination;
  Serial.println("Input a time between 1 and 100");
  Serial.setTimeout(10);
  while (!input) input = Serial.parseInt();
  Serial.println("Read value: ");
  Serial.println(input);
  delay(1000);
  percent = input < 100 ? input : 100;
  destination =   percent / 100.0;
  travel_to(destination);

}
