/**
*   @file   movement.c
*   @brief  a set of movement commands to use with the irobot
*   @author Ryan Majstorovic, Matt Smosna, Mekhi San
*   @date   02/05/2025
*/

#include "open_interface.h"
#include "movement.h"
#include "uart-interrupt.h"


float angle_correction_factor = 0.9;

/**
*   This function moves the irobot forward at the speed of 200mm/s.
*
*   @param  sensor_data passed in sensor data
*   @param  distance_mm distance the robot should move
*
*   @date   02/05/2025
*/

void move_forward_bump_interrupt(oi_t *sensor_data, double target_distance_mm) {
    static int state = 0;
    static double distance_sum = 0;


    switch (state) {
        case 0: // Start movement
            distance_sum = 0;
            oi_setWheels(100, 100);
            state = 1;
            break;

        case 1: // Monitor progress
            oi_update(sensor_data);
            distance_sum += sensor_data->distance;

            if (sensor_data->bumpLeft) {
                oi_setWheels(0, 0);
                state = 2;
            } else if (sensor_data->bumpRight) {
                oi_setWheels(0, 0);
                state = 3;
            } else if (distance_sum >= target_distance_mm) {
                oi_setWheels(0, 0);
                state = 4;
            }
            break;

        case 2: // Avoid right
            avoid_right(sensor_data);
            prev_command_flag = move_flag;
            command_flag = scan_flag;
            break;

        case 3: // Avoid left
            avoid_left(sensor_data);
            prev_command_flag = move_flag;
            command_flag = scan_flag;
            break;

        case 4: // Finished

            state = 0;
            break;
    }
}



void  move_forward (oi_t  *sensor_data,   double distance_mm){

    double sum = 0; // sum variable with same variable type as passed in sensor data
    oi_setWheels(200,200); //move forward at 2/5 speed

    while (sum < distance_mm) { //while loop counts up to distance_mm while robot moves forward

        oi_update(sensor_data);
        sum += sensor_data -> distance;

    }
    oi_setWheels(0,0); //stop

}

/**
*   This function moves the irobot backward at the speed of 200mm/s.
*
*   @param  sensor_data passed in sensor data
*   @param  distance_mm distance the robot should move should be a positive number
*
*   @date   02/05/2025
*/

void  move_backward (oi_t  *sensor_data, double distance_mm){

    double sum = 0; // sum variable with same variable type as passed in sensor data
    oi_setWheels(-200,-200); //move backward at 2/5 speed

    while (sum < distance_mm) { //while loop counts up to distance_mm while robot moves backward

        oi_update(sensor_data);
        sum -= sensor_data -> distance; // subtracts from sum given that distance returns a negative number when reversing to facilitate counting up

    }
    oi_setWheels(0,0); //stop

}

/**
*   This function moves the irobot forward while including obstacle detection and avoidance.
*
*   @param  sensor_data passed in sensor data
*   @param  distance_mm distance the robot should move
*
*   @date   02/05/2025
*/



/**
*   This function move the irobot in an avoidance maneuver backing up 15 cm then shifting over 25cm.
*
*   @param  sensor_data passed in sensor data
*
*   @date   02/05/2025
*/

void avoid_right(oi_t  *sensor_data){

    oi_setWheels(0,0);

    move_backward(sensor_data , 150);

    turn_right(sensor_data , 90);

    move_forward(sensor_data , 150);

    turn_left(sensor_data , 90);

    move_forward(sensor_data , 75);


}

/**
*   This function move the irobot in an avoidance maneuver backing up 15 cm then shifting over 25cm.
*
*   @param  sensor_data passed in sensor data
*
*   @date   02/05/2025
*/

void avoid_left(oi_t  *sensor_data){

    oi_setWheels(0,0);

    move_backward(sensor_data , 150);

    turn_left(sensor_data , 90);

    move_forward(sensor_data , 150);

    turn_right(sensor_data , 90);

    move_forward(sensor_data , 75);

}

/**
*   This function turns the irobot right based on the passed in degree angle.
*
*   @param  sensor_data passed in sensor data
*   @param  degrees angle in degrees the robot should turn
*
*   @date   02/05/2025
*/

void  turn_right (oi_t  *sensor_data , double degrees){

    double sum = 0; // sum variable with same variable type as passed in sensor data
    oi_setWheels(-100,100); //move forward at full speed
    double corrected_degrees = degrees * angle_correction_factor;

    while (sum < corrected_degrees) {

        oi_update(sensor_data);
        sum -= sensor_data -> angle; // use -> notation since pointer

    }

    oi_setWheels(0,0); //stop
}

/**
*   This function turns the irobot left based on the passed in degree angle.
*
*   @param  sensor_data passed in sensor data
*   @param  degrees angle in degrees the robot should turn
*
*   @date   02/05/2025
*/

void  turn_left (oi_t  *sensor_data , double degrees){

    double corrected_degrees = degrees * angle_correction_factor;
    double sum = 0; // sum variable with same variable type as passed in sensor data

    oi_setWheels(100,-100); //move forward at full speed

    while (sum < corrected_degrees) {

        oi_update(sensor_data);
        sum += sensor_data -> angle; // use -> notation since pointer

    }

    oi_setWheels(0,0); //stop
}

//=====================================================
// Old Code
//=====================================================
/*

void  move_forward_bump (oi_t  *sensor_data,   double distance_mm){

    double sum = 0; // sum variable with same variable type as passed in sensor data
    oi_setWheels(100,100); //move forward at 1/5 speed to allow for sensing

    while (sum < distance_mm) {

        oi_update(sensor_data);
        sum += sensor_data -> distance;

        if (sensor_data -> bumpLeft == 1) {

            avoid_right(sensor_data);

        } else if (sensor_data -> bumpRight == 1) {

            avoid_left(sensor_data);

        }
    }

    oi_setWheels(0,0); //stop

}
*/

