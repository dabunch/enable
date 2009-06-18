#include "kiva_affine_helpers.h"
#include <stdio.h>

#define f_eq(a,b)  (fabs((a)-(b)) < epsilon)

namespace kiva
{
    bool is_identity(agg::trans_affine& mat, double epsilon)
    {
        double temp[6];
        mat.store_to(temp);
		return (f_eq(temp[0], 1.0) && f_eq(temp[1], 0.0) &&
				f_eq(temp[2], 0.0) && f_eq(temp[3], 1.0) &&
				f_eq(temp[4], 0.0) && f_eq(temp[5], 0.0));
//        return (temp[0] == 1.0 && temp[1] == 0.0 &&
//                temp[2] == 0.0 && temp[3] == 1.0 &&
//                temp[4] == 0.0 && temp[5] == 0.0);

    }

    bool only_translation(agg::trans_affine& mat, double epsilon)
    {
        double temp[6];
        mat.store_to(temp);
		return (f_eq(temp[0], 1.0) && f_eq(temp[1], 0.0) &&
				f_eq(temp[2], 0.0) && f_eq(temp[3], 1.0));
    }

    bool only_scale_and_translation(agg::trans_affine& mat, double epsilon)
    {
        double temp[6];
        mat.store_to(temp);
        return (f_eq(temp[1], 0.0) && f_eq(temp[2], 0.0));
    }

    void get_translation(agg::trans_affine& m, double* tx, double* ty)
    {
        double temp[6];
        m.store_to(temp);
        *tx = temp[4];
        *ty = temp[5];
    }
}
