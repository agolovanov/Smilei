
#ifndef ELECTROMAGNBC_H
#define ELECTROMAGNBC_H

#include <vector>

#include "Patch.h"

class Params;
class LaserParams;
class Patch;
class ElectroMagn;
class LaserProfile;
class Field;

class ElectroMagnBC {
public:
    ElectroMagnBC( Params &params,  LaserParams &laser_params, Patch* patch );
    virtual ~ElectroMagnBC();

    virtual void apply_xmin(ElectroMagn* EMfields, double time_dual, Patch* patch) = 0;
    virtual void apply_xmax(ElectroMagn* EMfields, double time_dual, Patch* patch) = 0;
    virtual void apply_ymin(ElectroMagn* EMfields, double time_dual, Patch* patch) = 0;
    virtual void apply_ymax(ElectroMagn* EMfields, double time_dual, Patch* patch) = 0;
    void laserDisabled();

    virtual void save_fields_BC1D(Field*) {};
    virtual void save_fields_BC2D_Long(Field*) {};
    virtual void save_fields_BC2D_Trans(Field*) {};
    
 protected:

    //! Vector for the various lasers
    std::vector<LaserProfile*> laser_;
    
    //! time-step
    double dt;

};

#endif

