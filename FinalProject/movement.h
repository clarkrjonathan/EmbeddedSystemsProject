/*
 * movement.h
 *
 *  Created on: Feb 5, 2025
 *      Author: ryanmaj
 */

#ifndef MOVEMENT_H_
#define MOVEMENT_H_

void move_forward_bump_interrupt(oi_t *sensor_data, double target_distance_mm);

void  move_forward (oi_t  *sensor_data,   double distance_mm);

void  move_backward (oi_t  *sensor_data,   double distance_mm);

void  move_forward_bump (oi_t  *sensor_data,   double distance_mm);

void avoid_left(oi_t  *sensor_data);

void avoid_right(oi_t  *sensor_data);

void  turn_right (oi_t  *sensor_data , double degrees);

void  turn_left (oi_t  *sensor_data , double degrees);




#endif /* MOVEMENT_H_ */
