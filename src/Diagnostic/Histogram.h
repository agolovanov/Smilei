#ifndef HISTOGRAM_H
#define HISTOGRAM_H

#include "Species.h"
#include "SimWindow.h"


// Class for each axis of the particle diags
class HistogramAxis {
public:
    HistogramAxis() {};
    ~HistogramAxis() {};
    
    void init(std::string, double, double, int, bool, bool, std::vector<double>);
    
    //! Function that goes through the particles and find where they should go in the axis
    virtual void digitize(Species *, std::vector<double>&, std::vector<int>&, unsigned int, SimWindow*) {};
    
    //! quantity of the axis (e.g. 'x', 'px', ...)
    std::string type;
    
    //! starting/ending point for the axis binning
    double min, max;
    //! starting/ending point for the axis binning, accounting for logscale
    double actual_min, actual_max;
    //! number of bins for the axis binning
    int nbins;
    
    //! determines whether linear scale or log scale
    bool logscale;
    
    //! determines whether particles beyond min and max are counted in the first and last bin
    bool edge_inclusive;
    
    double coeff;
    
    //! List of coefficients (a,b,c) for a "composite" type of the form "ax+by+cz"
    std::vector<double> coefficients;
};


// Class for making a histogram of particle data
class Histogram {
public:
    Histogram() {};
    ~Histogram() {};
    
    void init(Params&, std::vector<PyObject*>, std::vector<unsigned int>, std::string, Patch*, std::vector<std::string>);
    
    //! Compute the index of each particle in the final histogram
    void digitize(Species *, std::vector<double>&, std::vector<int>&, SimWindow*);
    //! Calculate the quantity of each particle to be summed in the histogram
    virtual void valuate(Species*, std::vector<double>&, std::vector<int>&) {};
    //! Add the contribution of each particle in the histogram
    void distribute(std::vector<double>&, std::vector<int>&, std::vector<double>&);
    
    std::vector<HistogramAxis*> axes;
};



class HistogramAxis_x : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for ( unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Position[0][ipart];
        }
    };
};
class HistogramAxis_moving_x : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        double x_moved = simWindow->getXmoved();
        for ( unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Position[0][ipart]-x_moved;
        }
    };
};
class HistogramAxis_y : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Position[1][ipart];
        }
    };
};
class HistogramAxis_z : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Position[2][ipart];
        }
    };
};
class HistogramAxis_vector : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        unsigned int idim, ndim = coefficients.size()/2;
        for ( unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = 0.;
            for( idim=0; idim<ndim; idim++ )
                array[ipart] += (s->particles->Position[idim][ipart] - coefficients[idim]) * coefficients[idim+ndim];
        }
    };
};
class HistogramAxis_theta2D : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        double X,Y;
        for ( unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            X = s->particles->Position[0][ipart] - coefficients[0];
            Y = s->particles->Position[1][ipart] - coefficients[1];
            array[ipart] = atan2(coefficients[2]*Y - coefficients[3]*X, coefficients[2]*X + coefficients[3]*Y);
        }
    };
};
class HistogramAxis_theta3D : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for ( unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = (s->particles->Position[0][ipart] - coefficients[0]) * coefficients[3]
                         + (s->particles->Position[1][ipart] - coefficients[1]) * coefficients[4]
                         + (s->particles->Position[2][ipart] - coefficients[2]) * coefficients[5];
            if      ( array[ipart]> 1. ) array[ipart] = 0.;
            else if ( array[ipart]<-1. ) array[ipart] = M_PI;
            else array[ipart] = acos(array[ipart]);
        }
    };
};
class HistogramAxis_phi : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        unsigned int idim;
        double a, b;
        for ( unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            a = 0.;
            b = 0.;
            for( idim=0; idim<3; idim++ ) {
                a += (s->particles->Position[idim][ipart] - coefficients[idim]) * coefficients[idim+3];
                b += (s->particles->Position[idim][ipart] - coefficients[idim]) * coefficients[idim+6];
            }
            array[ipart] = atan2(b,a);
        }
    };
};
class HistogramAxis_px : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Momentum[0][ipart];
        }
    };
};
class HistogramAxis_py : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Momentum[1][ipart];
        }
    };
};
class HistogramAxis_pz : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Momentum[2][ipart];
        }
    };
};
class HistogramAxis_p : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * sqrt(pow(s->particles->Momentum[0][ipart],2)
                                        + pow(s->particles->Momentum[1][ipart],2)
                                        + pow(s->particles->Momentum[2][ipart],2));
        }
    };
};
class HistogramAxis_gamma : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class HistogramAxis_ekin : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * (sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                               + pow(s->particles->Momentum[1][ipart],2)
                                               + pow(s->particles->Momentum[2][ipart],2) ) - 1.);
        }
    };
};
class HistogramAxis_vx : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Momentum[0][ipart]
                           / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                      + pow(s->particles->Momentum[1][ipart],2)
                                      + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class HistogramAxis_vy : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Momentum[1][ipart]
                           / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                      + pow(s->particles->Momentum[1][ipart],2)
                                      + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class HistogramAxis_vz : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Momentum[2][ipart]
                           / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                      + pow(s->particles->Momentum[1][ipart],2)
                                      + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class HistogramAxis_v : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = pow( 1. + 1./(pow(s->particles->Momentum[0][ipart],2)
                                       + pow(s->particles->Momentum[1][ipart],2)
                                       + pow(s->particles->Momentum[2][ipart],2)) , -0.5);
        }
    };
};
class HistogramAxis_vperp2 : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = (  pow(s->particles->Momentum[1][ipart],2)
                            + pow(s->particles->Momentum[2][ipart],2)
                           ) / (1. + pow(s->particles->Momentum[0][ipart],2)
                                   + pow(s->particles->Momentum[1][ipart],2)
                                   + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class HistogramAxis_charge : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = (double) s->particles->Charge[ipart];
        }
    };
};
class HistogramAxis_chi : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Chi[ipart];
        }
    };
};
class HistogramAxis_composite : public HistogramAxis {
    void digitize(Species * s, std::vector<double>&array, std::vector<int>&index, unsigned int npart, SimWindow* simWindow) {
        unsigned int idim, ndim = coefficients.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = 0.;
            for (idim = 0 ; idim < ndim ; idim++)
                array[ipart] += coefficients[idim] * s->particles->Position[idim][ipart];
        }
    };
};


//! Children classes, for various manners to fill the histogram
class Histogram_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Weight[ipart];
        }
    };
};
class Histogram_charge_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Weight[ipart] * (double)(s->particles->Charge[ipart]);
        }
    };
};
class Histogram_jx_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Weight[ipart] * (double)(s->particles->Charge[ipart])
                         * s->particles->Momentum[0][ipart]
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_jy_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Weight[ipart] * (double)(s->particles->Charge[ipart])
                         * s->particles->Momentum[1][ipart]
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_jz_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->particles->Weight[ipart] * (double)(s->particles->Charge[ipart])
                         * s->particles->Momentum[2][ipart]
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_ekin_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * ( sqrt(1. + pow(s->particles->Momentum[0][ipart],2)
                                     + pow(s->particles->Momentum[1][ipart],2)
                                     + pow(s->particles->Momentum[2][ipart],2)) - 1.);
        }
    };
};
class Histogram_p_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * sqrt(pow(s->particles->Momentum[0][ipart],2)
                              + pow(s->particles->Momentum[1][ipart],2)
                              + pow(s->particles->Momentum[2][ipart],2));
        }
    };
};
class Histogram_px_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart] * s->particles->Momentum[0][ipart];
        }
    };
};
class Histogram_py_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart] * s->particles->Momentum[1][ipart];
        }
    };
};
class Histogram_pz_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart] * s->particles->Momentum[2][ipart];
        }
    };
};
class Histogram_pressure_xx : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * pow(s->particles->Momentum[0][ipart],2)
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_pressure_yy : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * pow(s->particles->Momentum[1][ipart],2)
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_pressure_zz : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * pow(s->particles->Momentum[2][ipart],2)
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_pressure_xy : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * s->particles->Momentum[0][ipart]
                         * s->particles->Momentum[1][ipart]
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_pressure_xz : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * s->particles->Momentum[0][ipart]
                         * s->particles->Momentum[2][ipart]
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_pressure_yz : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * s->particles->Momentum[1][ipart]
                         * s->particles->Momentum[2][ipart]
                         / sqrt( 1. + pow(s->particles->Momentum[0][ipart],2)
                                    + pow(s->particles->Momentum[1][ipart],2)
                                    + pow(s->particles->Momentum[2][ipart],2) );
        }
    };
};
class Histogram_ekin_vx_density : public Histogram {
    void valuate(Species * s, std::vector<double> &array, std::vector<int> &index) {
        unsigned int npart = array.size();
        for (unsigned int ipart = 0 ; ipart < npart ; ipart++) {
            if( index[ipart]<0 ) continue;
            array[ipart] = s->mass * s->particles->Weight[ipart]
                         * s->particles->Momentum[0][ipart]
                         * (1. - 1./sqrt(1. + pow(s->particles->Momentum[0][ipart],2)
                                            + pow(s->particles->Momentum[1][ipart],2)
                                            + pow(s->particles->Momentum[2][ipart],2)));
        }
    };
};


#endif

