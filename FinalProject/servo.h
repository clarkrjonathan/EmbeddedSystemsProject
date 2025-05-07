/*
 * servo.h
 *
 *  Created on: Apr 14, 2025
 *      Author: jclark15
 */

#ifndef SERVO_H_
#define SERVO_H_

#include <inc/tm4c123gh6pm.h>
#include <stdint.h>

void servo_init(void);


void servo_move(float);

void setPulseLength(uint32_t);

void servo_calibrate(void);

void servo_setPulseLength(uint32_t);
void servo_moveNonBlocking(float degrees);

#endif /* SERVO_H_ */

