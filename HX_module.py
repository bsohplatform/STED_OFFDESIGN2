from scipy.special import ellipe
from math import pi
import numpy as np
from CoolProp.CoolProp import PropsSI
from Correlation import PHX

class HX_module:
    def __init__(self, hx_type, cor, Inputs):
        self.cor = cor
        if hx_type == 'phx':
            self.phx_inputs = Inputs
            if cor == True:
                self.pitch_p = self.phx_inputs.pitch_p
                self.pitch_s = self.phx_inputs.pitch_s
                self.spacing_p = self.pitch_p - self.phx_inputs.thk_plate
                self.spacing_s = self.pitch_s - self.phx_inputs.thk_plate
                self.crg_pitch_p = self.phx_inputs.crg_pitch_p
                self.crg_pitch_s = self.phx_inputs.crg_pitch_s
                self.enlargement_p = self.phx_inputs.enlargement_p
                self.enlargement_s = self.phx_inputs.enlargement_s
                self.Nch_p = (self.phx_inputs.N_plate-1)/2 if self.phx_inputs.Nch_p == 0 else self.phx_inputs.Nch_p
                self.Nch_s = (self.phx_inputs.N_plate-1)/2 if self.phx_inputs.Nch_s == 0 else self.phx_inputs.Nch_s
                self.Acx_p = self.spacing_p*self.phx_inputs.L_width*self.Nch_p
                self.Acx_s = self.spacing_s*self.phx_inputs.L_width*self.Nch_s
                self.Dh_p = 2*self.spacing_p/self.enlargement_p
                self.Dh_s = 2*self.spacing_s/self.enlargement_s
                self.R_plate = self.phx_inputs.thk_plate/self.phx_inputs.k
                self.A_flow = self.phx_inputs.L_width*self.phx_inputs.L_vert*(self.enlargement_p+self.enlargement_s)*min(self.phx_inputs.Nch_s,self.phx_inputs.Nch_p) if self.phx_inputs.A_flow == 0 else self.phx_inputs.A_flow
                self.A_flow = self.A_flow*self.phx_inputs.mult_A
                self.V_p = self.spacing_p*self.phx_inputs.L_width*self.phx_inputs.L_vert*self.phx_inputs.Nch_p if self.phx_inputs.V_p == 0 else self.phx_inputs.V_p
                self.V_s = self.spacing_s*self.phx_inputs.L_width*self.phx_inputs.L_vert*self.phx_inputs.Nch_s if self.phx_inputs.V_s == 0 else self.phx_inputs.V_s
                self.beta = 60.0 if self.phx_inputs.beta == 0 else self.phx_inputs.beta
            else:
                self.V_p = 1.0
        elif hx_type == 'fthx':
            self.fthx_inputs = Inputs
            if cor == True:
                self.Dh = self.fthx_inputs.Dh
                Acx_p = self.Dh**2*pi/4
                self.A_flow = 2*pi*self.Dh*self.fthx_inputs.L_pass
                self.V = self.Dh**2*pi/4*self.fthx_inputs.L_pass*self.fthx_inputs.N_turn*self.fthx_inputs.N_row
            else:
                self.V = 1.0
        else:
            print('Undefined HX type is entered')

    def PHX(self, purpose, primary_in, primary_out, secondary_in, secondary_out):
        cor = self.cor
        
        G_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        x_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        T_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        h_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        htc_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        Re_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        pr_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        f_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        p_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        d_primary = np.zeros(shape=(self.phx_inputs.N_element+1))
        
        T_secondary = np.zeros(shape=(self.phx_inputs.N_element+1))    
        
        UA_tot = np.zeros(shape=(self.phx_inputs.N_element+1))
        eps = np.zeros(shape=(self.phx_inputs.N_element+1))
        Q_trans = np.zeros(shape=(self.phx_inputs.N_element+1))
        
        # Initial setting
        T_sec_lb = secondary_out.T
        T_sec_ub = secondary_out.T
        c_sec = secondary_out.c
        v_sec = secondary_out.v
        l_sec = secondary_out.l
        pr_sec = secondary_out.pr
        mdot_sec = secondary_out.m
        
        if cor == False:
            #UA = self.phx_inputs.UA*pow(primary_in.m/self.phx_inputs.mdot_nominal_ref,0.8)
            UA = self.phx_inputs.UA
        
        T_primary[0] = primary_in.T
        h_primary[0] = primary_in.h
        p_primary[0] = primary_in.p
        hl_primary = primary_in.hl
        hg_primary = primary_in.hg
        
        x_primary[0] = (h_primary[0]-hl_primary)/(hg_primary - hl_primary)
        
        if x_primary[0] > 0 and x_primary[0] < 1:
            dl_primary = PropsSI('D','P',p_primary[0],'Q',0.0, primary_in.Y)
            dg_primary = PropsSI('D','P',p_primary[0],'Q',1.0, primary_in.Y)
            d_primary[0] = 1/(x_primary[0]/dg_primary+(1-x_primary[0])/dl_primary)
        else:
            d_primary[0] = PropsSI('D','T',T_primary[0],'P',p_primary[0],primary_in.Y)
            c_primary = PropsSI('C','T',T_primary[0],'P',p_primary[0],primary_in.Y)
                
        if cor == True:
            Acx_p = self.Acx_p
            Acx_s = self.Acx_s
            Dh_p = self.Dh_p
            Dh_s = self.Dh_s
            beta = self.beta
            enlargement_p = self.enlargement_p
            enlargement_s = self.enlargement_s
            
            G_primary_ref = primary_in.m/Acx_p
            if x_primary[0] > 0 and x_primary[0] < 1:
                vl_primary = PropsSI('V','P',p_primary[0],'Q',0.0, primary_in.Y)
                vg_primary = PropsSI('V','P',p_primary[0],'Q',1.0, primary_in.Y)
                cl_primary = PropsSI('C','P',p_primary[0],'Q',0.0, primary_in.Y)
                ll_primary = PropsSI('L','P',p_primary[0],'Q',0.0, primary_in.Y)
                
                G_primary[0] = G_primary_ref*((1-x_primary[0])+x_primary[0]*pow(dl_primary/dg_primary,0.5))
                Re_primary[0] = G_primary[0]*Dh_p/vl_primary
                pr_primary[0] = cl_primary*vl_primary/ll_primary
            else:
                v_primary = PropsSI('V','T',T_primary[0],'P',p_primary[0],primary_in.Y)
                l_primary = PropsSI('L','T',T_primary[0],'P',p_primary[0],primary_in.Y)
                
                G_primary[0] = G_primary_ref
                Re_primary[0] = G_primary_ref*Dh_p/v_primary
                pr_primary[0] = c_primary*v_primary/l_primary
        
        T_sec = 0.5*(T_sec_lb + T_sec_ub)
        
        T_secondary[0] = T_sec
        
        dT = T_primary[0]-T_secondary[0]
        if (dT < 0.0 and purpose == 'cond') or (dT > 0.0 and purpose == 'evap'):
            err_index = 1 # Temperature Reverse
            Q = 0
            mean_d = 0
            T_pp = 0
        else:
            err_index = 0

            if cor == True:
                if x_primary[0] > 0 and x_primary[0] < 1:
                    qq = 10*dT
                    while 1:
                        if purpose == 'cond':
                            (htc_primary[0], f_primary[0]) = PHX.cor_cond_2ph(p_primary[0],primary_in.pcr,qq,G_primary_ref,Re_primary[0],pr_primary[0],hl_primary,hg_primary,ll_primary,vl_primary,Dh_p)
                        else:
                            i_primary = PropsSI('I','H',h_primary[0],'P',p_primary[0],primary_in.Y)
                            (htc_primary[0], f_primary[0]) = PHX.cor_evap_2ph(abs(qq), x_primary[0], G_primary_ref, G_primary[0], hl_primary,hg_primary,dl_primary,dg_primary,ll_primary,vl_primary,vg_primary,i_primary,Dh_p,beta)
                            
                        G_secondary = mdot_sec/self.Acx_s
                        Re_secondary = G_secondary*Dh_s/v_sec
                        
                        (htc_secondary, f_secondary) = PHX.cor_1ph(Re_secondary,pr_sec,l_sec,1.0, Dh_s, beta, enlargement_s)
                        
                        qq_cal = 1/(1/(htc_primary[0]*self.phx_inputs.mult_pri)+self.R_plate+1/(htc_secondary*self.phx_inputs.mult_sec))*dT
                        
                        if abs(qq-qq_cal)/qq_cal < 1.0e-4:
                            break
                        else:
                            qq = qq_cal
                else:
                    try:
                        v_ratio = v_primary/PropsSI('V','T',T_secondary[0],'P',p_primary[0],primary_in.Y)
                    except:
                        v_ratio = 1
                        
                    (htc_primary[0], f_primary[0]) = PHX.cor_1ph(Re_primary[0],pr_primary[0],l_primary,v_ratio, Dh_p, beta, enlargement_p)
                    
                    G_secondary = mdot_sec/self.Acx_s
                    Re_secondary = G_secondary*Dh_s/v_sec
                    (htc_secondary, f_secondary) = PHX.cor_1ph(Re_secondary,pr_sec,l_sec,1.0, Dh_s, beta, enlargement_s)

                UA_tot[0] = self.A_flow/(self.phx_inputs.N_element-1)/(1/(htc_primary[0]*self.phx_inputs.mult_pri)+self.R_plate+1/(htc_secondary*self.phx_inputs.mult_sec))
                dp_primary = f_primary[0]*G_primary[0]**2*self.phx_inputs.L_vert/(self.phx_inputs.N_element-1)/(d_primary[0]*Dh_p)/2                
            else:
                UA_const = UA/(self.phx_inputs.N_element)
                dp_const = self.phx_inputs.dp/(self.phx_inputs.N_element)*primary_in.p
                
                UA_tot[0] = UA_const
                dp_primary = dp_const
                
                
            if x_primary[0] > 0 and x_primary[0] < 1:
                C_min = c_sec*mdot_sec
                NTU = UA_tot[0]/C_min
                eps[0] = 1 - np.exp(-NTU)
            else:
                C_min = min(c_primary*primary_in.m, c_sec*mdot_sec)
                C_max = max(c_primary*primary_in.m, c_sec*mdot_sec)
                C_r = C_min/C_max
                NTU = UA_tot[0]/C_min
                eps[0] = (1-np.exp(-(1-C_r)*NTU))/(1-C_r*np.exp(-(1-C_r)*NTU))
            
            Q_trans[0] = eps[0]*C_min*((T_primary[0] - T_secondary[0]))
            
            for jj in range(self.phx_inputs.N_element):
                h_primary[jj+1] = h_primary[jj] - Q_trans[jj]/primary_in.m
                T_secondary[jj+1] = T_secondary[jj] - Q_trans[jj]/(c_sec*mdot_sec)
                p_primary[jj+1] = p_primary[jj] - dp_primary
                
                hl_primary = PropsSI('H','P',p_primary[jj+1],'Q',0.0, primary_in.Y)
                hg_primary = PropsSI('H','P',p_primary[jj+1],'Q',1.0, primary_in.Y)
                
                x_primary[jj+1] = (h_primary[jj+1]-hl_primary)/(hg_primary - hl_primary)
                
                T_primary[jj+1] = PropsSI('T','H',h_primary[jj+1],'P',p_primary[jj+1],primary_in.Y)
                dT = T_primary[jj+1]-T_secondary[jj+1]        

                if x_primary[jj+1] > 0 and x_primary[jj+1] < 1:
                    dl_primary = PropsSI('D','P',p_primary[jj+1],'Q',0.0, primary_in.Y)
                    dg_primary = PropsSI('D','P',p_primary[jj+1],'Q',1.0, primary_in.Y)
                    d_primary[jj+1] = 1/(x_primary[jj+1]/dg_primary+(1-x_primary[jj+1])/dl_primary)
                else:
                    d_primary[jj+1] = PropsSI('D','T',T_primary[jj+1],'P',p_primary[jj+1],primary_in.Y)
                    c_primary = PropsSI('C','T',T_primary[jj+1],'P',p_primary[jj+1],primary_in.Y)
                    
                if cor == True:
                    if x_primary[jj+1] > 0 and x_primary[jj+1] < 1:
                        vl_primary = PropsSI('V','P',p_primary[jj+1],'Q',0.0, primary_in.Y)
                        vg_primary = PropsSI('V','P',p_primary[jj+1],'Q',1.0, primary_in.Y)
                        cl_primary = PropsSI('C','P',p_primary[jj+1],'Q',0.0, primary_in.Y)
                        ll_primary = PropsSI('L','P',p_primary[jj+1],'Q',0.0, primary_in.Y)
                        
                        G_primary[jj+1] = G_primary_ref*((1-x_primary[jj+1])+x_primary[jj+1]*pow(dl_primary/dg_primary,0.5))
                        Re_primary[jj+1] = G_primary[jj+1]*Dh_p/vl_primary
                        pr_primary[jj+1] = cl_primary*vl_primary/ll_primary
                        
                        qq = UA_tot[jj]*dT/(self.A_flow/(self.phx_inputs.N_element-1))
                        while 1:
                            if purpose == 'cond':
                                (htc_primary[jj+1], f_primary[jj+1]) = PHX.cor_cond_2ph(p_primary[jj+1],primary_in.pcr,qq,G_primary_ref,Re_primary[jj+1],pr_primary[jj+1],hl_primary,hg_primary,ll_primary,vl_primary,Dh_p)
                            else:
                                i_primary = PropsSI('I','H',h_primary[jj+1],'P',p_primary[jj+1],primary_in.Y)
                                (htc_primary[jj+1], f_primary[jj+1]) = PHX.cor_evap_2ph(abs(qq), x_primary[jj+1], G_primary_ref, G_primary[jj+1], hl_primary,hg_primary,dl_primary,dg_primary,ll_primary,vl_primary,vg_primary,i_primary,Dh_p,beta)
                                
                            G_secondary = mdot_sec/Acx_s
                            Re_secondary = G_secondary*Dh_s/v_sec
                            
                            (htc_secondary, f_secondary) = PHX.cor_1ph(Re_secondary,pr_sec,l_sec,1.0, Dh_s, beta, enlargement_s)
                            
                            qq_cal = 1/(1/(htc_primary[jj+1]*self.phx_inputs.mult_pri)+self.R_plate+1/(htc_secondary*self.phx_inputs.mult_sec))*dT
                            
                            if abs(qq-qq_cal)/qq_cal < 1.0e-4:
                                break
                            else:
                                qq = qq_cal
                    else:
                        v_primary = PropsSI('V','T',T_primary[jj+1],'P',p_primary[jj+1],primary_in.Y)
                        l_primary = PropsSI('L','T',T_primary[jj+1],'P',p_primary[jj+1],primary_in.Y)    
                        
                        G_primary[jj+1] = G_primary_ref
                        Re_primary[jj+1] = G_primary_ref*Dh_p/v_primary
                        pr_primary[jj+1] = c_primary*v_primary/l_primary
                        
                        try:
                            v_ratio = v_primary/PropsSI('V','T',T_secondary[jj+1],'P',p_primary[jj+1],primary_in.Y)
                        except:
                            v_ratio = 1
                            
                        (htc_primary[jj+1], f_primary[jj+1]) = PHX.cor_1ph(Re_primary[jj+1],pr_primary[jj+1],l_primary,v_ratio, Dh_p, beta, enlargement_p)
                        
                        G_secondary = mdot_sec/Acx_s
                        Re_secondary = G_secondary*Dh_s/v_sec
                        (htc_secondary, f_secondary) = PHX.cor_1ph(Re_secondary,pr_sec,l_sec,1.0, Dh_s, beta, enlargement_s)
        
                    UA_tot[jj+1] = self.A_flow/(self.phx_inputs.N_element-1)/(1/(htc_primary[jj+1]*self.phx_inputs.mult_pri)+self.R_plate+1/(htc_secondary*self.phx_inputs.mult_sec))
                    dp_primary = f_primary[jj+1]*G_primary[jj+1]**2*self.phx_inputs.L_vert/(self.phx_inputs.N_element-1)/(d_primary[jj+1]*Dh_p)/2
                else:                        
                    UA_tot[jj+1] = UA_const
                    dp_primary = dp_const
                
                if x_primary[jj+1] > 0 and x_primary[jj+1] < 1:
                    C_min = c_sec*mdot_sec
                    NTU = UA_tot[jj+1]/C_min
                    eps[jj+1] = 1 - np.exp(-NTU)
                else:
                    C_min = min(c_primary*primary_in.m, c_sec*mdot_sec)
                    C_max = max(c_primary*primary_in.m, c_sec*mdot_sec)
                    C_r = C_min/C_max
                    NTU = UA_tot[jj+1]/C_min
                    eps[jj+1] = (1-np.exp(-(1-C_r)*NTU))/(1-C_r*np.exp(-(1-C_r)*NTU))
                
                Q_trans[jj+1] = eps[jj+1]*C_min*(T_primary[jj+1] - T_secondary[jj+1])
        
            T_secondary_cal = T_secondary[-1]
            secondary_in.T = T_secondary_cal.item()
            
            mean_d = d_primary.mean().item()
            
            primary_out.T=T_primary[-1].item()
            primary_out.p=p_primary[-1].item()
            try:
                primary_out.Ts=PropsSI('T','P',primary_out.p,'Q',0.5,primary_out.Y)
            except:
                primary_out.Ts = primary_out.T
            primary_out.h=h_primary[-1].item()
            primary_out.hl=hl_primary
            primary_out.hg=hg_primary
            
            secondary_in.T = T_secondary[-1].item()
            secondary_out.T = T_sec
            
            self.Qp = (h_primary[0] - h_primary[-1])*primary_in.m
            self.Qs = c_sec*(T_secondary[0] - T_secondary[-1])*mdot_sec
            self.Qt = Q_trans.sum()
            Q = min([self.Qp, self.Qs, self.Qt]).item()
            T_pp = [abs(T1-T2) for T1, T2 in zip(T_primary, T_secondary)]
            T_pp = np.min(T_pp).item()
        
        return(primary_in, primary_out, secondary_in, secondary_out, Q, mean_d, T_pp, err_index)
    
    def FTHX(self, purpose, primary_in, primary_out, secondary_in, secondary_out, noHX):
        cor = self.cor
        
        N_element = self.fthx_inputs.N_element
        N_turn = self.fthx_inputs.N_turn
        N_row = self.fthx_inputs.N_row
        
        G_primary = np.zeros(shape=(N_element*N_turn, N_row))
        x_primary = np.zeros(shape=(N_element*N_turn, N_row))
        T_primary = np.zeros(shape=(N_element*N_turn, N_row))
        h_primary = np.zeros(shape=(N_element*N_turn, N_row))
        htc_primary = np.zeros(shape=(N_element*N_turn, N_row))
        Re_primary = np.zeros(shape=(N_element*N_turn, N_row))
        pr_primary = np.zeros(shape=(N_element*N_turn, N_row))
        f_primary = np.zeros(shape=(N_element*N_turn, N_row))
        p_primary = np.zeros(shape=(N_element*N_turn, N_row))
        d_primary = np.zeros(shape=(N_element*N_turn, N_row))
        
        T_secondary = np.zeros(shape=(N_element*N_turn, N_row))
        
        UA_tot = np.ones(shape=(N_element*N_turn, N_row))
        eps = np.zeros(shape=(N_element*N_turn, N_row))
        Q_trans = np.zeros(shape=(N_element*N_turn, N_row))
        
        if noHX == 0:
            T_sec_lb = secondary_out.T if purpose == 'evap' else secondary_out.T - 50.0
            T_sec_ub = secondary_out.T if purpose == 'cond' else secondary_out.T + 50.0
            c_sec = secondary_out.c
            v_sec = secondary_out.v
            l_sec = secondary_out.l
            pr_sec = secondary_out.pr
            try:
                mdot_sec = secondary_in.m
            except:
                mdot_sec = secondary_out.m
            if cor == False:
                #UA = self.fthx_inputs.UA*pow(mdot_sec/self.fthx_inputs.mdot_nominal_sec,0.8)
                UA = self.fthx_inputs.UA
            
        elif noHX == 1:
            T_sec_lb = secondary_in.T
            T_sec_ub = secondary_in.T
            
            c_sec = secondary_in.c
            v_sec = secondary_in.v
            l_sec = secondary_in.l
            pr_sec = secondary_in.pr
            try:
                mdot_sec = secondary_in.m
            except:
                mdot_sec = secondary_out.m
            if cor == False:
                #UA = self.fthx_inputs.UA*pow(mdot_sec/self.fthx_inputs.mdot_nominal_sec,0.8)
                UA = self.fthx_inputs.UA
                
        else:
            T_sec_lb = secondary_in.T
            T_sec_ub = secondary_in.T
            
            c_sec = 0.5*(secondary_in.c + secondary_out.c)
            v_sec = 0.5*(secondary_in.v + secondary_out.v)
            l_sec = 0.5*(secondary_in.l + secondary_out.l)
            pr_sec = c_sec*v_sec/l_sec
            
            mdot_sec_lb = 0;
            mdot_sec_ub = 3*(primary_in.hg - primary_in.hl)*primary_in.m/c_sec/(secondary_out.T - secondary_in.T) if purpose == 'cond' else 3*(primary_in.hg - primary_in.hl)*primary_in.m/c_sec/(secondary_in.T - secondary_out.T)
            if cor == False:
                UA = self.fthx_inputs.UA
                    
        T_primary_in = primary_in.T
        h_primary_in = primary_in.h
        p_primary_in = primary_in.p
        hl_primary_in = primary_in.hl
        hg_primary_in = primary_in.hg
        
        x_primary_in = (h_primary_in-hl_primary_in)/(hg_primary_in - hl_primary_in)
        
        if x_primary_in > 0 and x_primary_in < 1:
            dl_primary = PropsSI('D','P',p_primary_in,'Q',0.0, primary_in.Y)
            dg_primary = PropsSI('D','P',p_primary_in,'Q',1.0, primary_in.Y)
            d_primary_in = 1/(x_primary_in/dg_primary+(1-x_primary_in)/dl_primary)
        else:
            d_primary_in = PropsSI('D','T',T_primary_in,'P',p_primary_in,primary_in.Y)
            c_primary = PropsSI('C','T',T_primary_in,'P',p_primary_in,primary_in.Y)
        
        if cor == True:
            Dh = self.Dh
            '''
            T_primary[0,0] = primary_in.T
            h_primary[0,0] = primary_in.h
            p_primary[0,0] = primary_in.p
            hl_primary = primary_in.hl
            hg_primary = primary_in.hg
            
            x_primary[0,0] = (h_primary[0,0]-hl_primary)/(hg_primary - hl_primary)
            
            if cor == True:
                G_primary_ref = primary_in.m/Acx_p
                if x_primary[0,0] > 0 and x_primary[0,0] < 1:
                    dl_primary = PropsSI('D','P',p_primary[0,0],'Q',0.0, primary_in.Y)
                    dg_primary = PropsSI('D','P',p_primary[0,0],'Q',1.0, primary_in.Y)
                    d_primary[0,0] = 1/(x_primary[0,0]/dg_primary+(1-x_primary[0,0])/dl_primary)
                    vl_primary = PropsSI('V','P',p_primary[0,0],'Q',0.0, primary_in.Y)
                    vg_primary = PropsSI('V','P',p_primary[0,0],'Q',1.0, primary_in.Y)
                    cl_primary = PropsSI('C','P',p_primary[0,0],'Q',0.0, primary_in.Y)
                    ll_primary = PropsSI('L','P',p_primary[0,0],'Q',0.0, primary_in.Y)
                    
                    G_primary[0,0] = G_primary_ref*((1-x_primary[0,0])+x_primary[0,0]*pow(dl_primary/dg_primary,0.5))
                    Re_primary[0,0] = G_primary[0,0]*self.Dh/vl_primary
                    pr_primary[0,0] = cl_primary*vl_primary/ll_primary
                else:
                    d_primary[0,0] = PropsSI('D','T',T_primary[0,0],'P',p_primary[0,0],primary_in.Y)
                    v_primary = PropsSI('V','T',T_primary[0,0],'P',p_primary[0,0],primary_in.Y)
                    c_primary = PropsSI('C','T',T_primary[0,0],'P',p_primary[0,0],primary_in.Y)
                    l_primary = PropsSI('L','T',T_primary[0,0],'P',p_primary[0,0],primary_in.Y)
                    
                    G_primary[0,0] = G_primary_ref
                    Re_primary[0,0] = G_primary_ref*self.Dh/v_primary
                    pr_primary[0,0] = c_primary*v_primary/l_primary
            ''' # 나중에 상관식 정해지면 수정
            
        a_FTHX = 1
                
        while a_FTHX:
            T_sec = 0.5*(T_sec_lb + T_sec_ub)
            
            if noHX == 2:
                mdot_sec = 0.5*(mdot_sec_lb + mdot_sec_ub)
                #if cor == False:
                #    UA = self.fthx_inputs.UA*pow(mdot_sec/self.fthx_inputs.mdot_nominal_ref,0.8)
                    
            dT = primary_in.T - T_sec
            if (dT < 0.0 and purpose == 'cond') or (dT > 0.0 and purpose == 'evap'):
                err_index = 1 # Temperature Reverse
                break
            else:
                err_index = 0
            
            if cor == True:
                aaa = 0
            else:
                UA_const = UA/(N_element*N_turn*N_row)
                dp_const = self.fthx_inputs.dp/(N_element*N_turn*N_row)*primary_in.p
                UA_in = UA_const
                dp_in = dp_const
                
            if x_primary_in > 0 and x_primary_in < 1:
                C_min = c_sec*mdot_sec
                NTU = UA_in/C_min
                eps_in = 1 - np.exp(-NTU)
            else:
                C_min = min(c_primary*primary_in.m, c_sec*mdot_sec)
                C_max = max(c_primary*primary_in.m, c_sec*mdot_sec)
                C_r = C_min/C_max
                NTU = UA_in/C_min
                
                if C_min == c_primary*primary_in.m:
                    eps_in = 1-np.exp(-(1-np.exp(-NTU*C_r))/C_r)
                else:
                    eps_in = (1-np.exp(-C_r*(1-np.exp(-NTU))))/C_r
                    
            Q_trans_in = eps_in*C_min*((T_primary_in - T_sec))
            
            for rr in range(N_row):
                for tt in range(N_turn):
                    for jj in range(N_element):
                        if rr == 0:
                            if jj == 0:
                                h_primary[N_element*tt+jj,rr] = h_primary_in - Q_trans_in/primary_in.m
                                p_primary[N_element*tt+jj,rr] = p_primary_in - dp_in
                            else:
                                h_primary[N_element*tt+jj,rr] = h_primary[N_element*tt+jj-1,rr] - Q_trans[N_element*tt+jj-1,rr]/primary_in.m
                                p_primary[N_element*tt+jj,rr] = p_primary[N_element*tt+jj-1,rr] - dp_primary
                            
                            hl_primary = PropsSI('H','P',p_primary[N_element*tt+jj,rr],'Q',0.0, primary_in.Y)
                            hg_primary = PropsSI('H','P',p_primary[N_element*tt+jj,rr],'Q',1.0, primary_in.Y)
                            x_primary[N_element*tt+jj,rr] = (h_primary[N_element*tt+jj,rr]-hl_primary)/(hg_primary - hl_primary)
                            T_primary[N_element*tt+jj,rr] = PropsSI('T','H',h_primary[N_element*tt+jj,rr],'P',p_primary[N_element*tt+jj,rr],primary_in.Y)
                            dT = T_primary[N_element*tt+jj,rr]-T_sec
                            
                            if x_primary[N_element*tt+jj,rr] > 0 and x_primary[N_element*tt+jj,rr] < 1:
                                dl_primary = PropsSI('D','P',p_primary[N_element*tt+jj,rr],'Q',0.0, primary_in.Y)
                                dg_primary = PropsSI('D','P',p_primary[N_element*tt+jj,rr],'Q',1.0, primary_in.Y)
                                d_primary[N_element*tt+jj,rr] = 1/(x_primary[N_element*tt+jj,rr]/dg_primary+(1-x_primary[N_element*tt+jj,rr])/dl_primary)
                            else:
                                d_primary[N_element*tt+jj,rr] = PropsSI('D','T',T_primary[N_element*tt+jj,rr],'P',p_primary[N_element*tt+jj,rr],primary_in.Y)
                                c_primary = PropsSI('C','T',T_primary[N_element*tt+jj,rr],'P',p_primary[N_element*tt+jj,rr],primary_in.Y)
                            
                            if cor == True:
                                aaa = 1
                            else:
                                UA_tot[N_element*tt+jj,rr] = UA_const
                                dp_primary = dp_const
                                    
                            if x_primary[N_element*tt+jj,rr] > 0 and x_primary[N_element*tt+jj,rr] < 1:
                                C_min = c_sec*mdot_sec
                                NTU = UA_tot[N_element*tt+jj,rr]/C_min
                                eps[N_element*tt+jj,rr] = 1 - np.exp(-NTU)
                            else:
                                C_min = min(c_primary*primary_in.m, c_sec*mdot_sec)
                                C_max = max(c_primary*primary_in.m, c_sec*mdot_sec)
                                C_r = C_min/C_max
                                NTU = UA_tot[N_element*tt+jj,rr]/C_min
                                
                                if C_min == c_primary*primary_in.m:
                                    eps[N_element*tt+jj,rr] = 1-np.exp(-(1-np.exp(-NTU*C_r))/C_r)
                                else:
                                    eps[N_element*tt+jj,rr] = (1-np.exp(-C_r*(1-np.exp(-NTU))))/C_r
                                    
                            Q_trans[N_element*tt+jj,rr] = eps[N_element*tt+jj,rr]*C_min*((T_primary[N_element*tt+jj,rr] - T_sec))
                            
                            T_secondary[N_element*tt+jj,rr] = T_sec + Q_trans[N_element*tt+jj,rr]/(c_sec*mdot_sec/N_element/N_turn)
                            
                            if jj == N_element-1:
                                T_primary_in = T_primary[N_element*tt+jj,rr]
                                h_primary_in = h_primary[N_element*tt+jj,rr]
                                p_primary_in = p_primary[N_element*tt+jj,rr]
                                x_primary_in = (h_primary_in-hl_primary)/(hg_primary - hl_primary)
                                Q_trans_in = Q_trans[N_element*tt+jj,rr]
                                dp_in = dp_primary
                            
                        elif round(rr/2) != rr/2 and rr != 0:
                            if jj == 0:
                                h_primary[N_element*N_turn-1-N_element*tt-jj,rr] = h_primary_in - Q_trans_in/primary_in.m
                                p_primary[N_element*N_turn-1-N_element*tt-jj,rr] = p_primary_in - dp_in
                            else:
                                h_primary[N_element*N_turn-1-N_element*tt-jj,rr] = h_primary[N_element*N_turn-1-N_element*tt-jj+1,rr] - Q_trans[N_element*N_turn-1-N_element*tt-jj+1,rr]/primary_in.m
                                p_primary[N_element*N_turn-1-N_element*tt-jj,rr] = p_primary[N_element*N_turn-1-N_element*tt-jj+1,rr] - dp_primary
                                    
                            hl_primary = PropsSI('H','P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],'Q',0.0, primary_in.Y)
                            hg_primary = PropsSI('H','P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],'Q',1.0, primary_in.Y)
                            x_primary[N_element*N_turn-1-N_element*tt-jj,rr] = (h_primary[N_element*N_turn-1-N_element*tt-jj,rr]-hl_primary)/(hg_primary - hl_primary)
                            T_primary[N_element*N_turn-1-N_element*tt-jj,rr] = PropsSI('T','H',h_primary[N_element*N_turn-1-N_element*tt-jj,rr],'P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],primary_in.Y)
                            dT = T_primary[N_element*N_turn-1-N_element*tt-jj,rr]-T_secondary[N_element*N_turn-1-N_element*tt-jj,rr-1]
                            
                            if x_primary[N_element*N_turn-1-N_element*tt-jj,rr] > 0 and x_primary[N_element*N_turn-1-N_element*tt-jj,rr] < 1:
                                dl_primary = PropsSI('D','P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],'Q',0.0, primary_in.Y)
                                dg_primary = PropsSI('D','P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],'Q',1.0, primary_in.Y)
                                d_primary[N_element*N_turn-1-N_element*tt-jj,rr] = 1/(x_primary[N_element*N_turn-1-N_element*tt-jj,rr]/dg_primary+(1-x_primary[N_element*N_turn-1-N_element*tt-jj,rr])/dl_primary)
                            else:
                                d_primary[N_element*N_turn-1-N_element*tt-jj,rr] = PropsSI('D','T',T_primary[N_element*N_turn-1-N_element*tt-jj,rr],'P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],primary_in.Y)
                                c_primary = PropsSI('C','T',T_primary[N_element*N_turn-1-N_element*tt-jj,rr],'P',p_primary[N_element*N_turn-1-N_element*tt-jj,rr],primary_in.Y)
                            
                            if cor == True:
                                aaa = 1
                            else:
                                UA_tot[N_element*N_turn-1-N_element*tt-jj,rr] = UA_const
                                dp_primary = dp_const
                                    
                            if x_primary[N_element*N_turn-1-N_element*tt-jj,rr] > 0 and x_primary[N_element*N_turn-1-N_element*tt-jj,rr] < 1:
                                C_min = c_sec*mdot_sec
                                NTU = UA_tot[N_element*N_turn-1-N_element*tt-jj,rr]/C_min
                                eps[N_element*N_turn-1-N_element*tt-jj,rr] = 1 - np.exp(-NTU)
                            else:
                                C_min = min(c_primary*primary_in.m, c_sec*mdot_sec)
                                C_max = max(c_primary*primary_in.m, c_sec*mdot_sec)
                                C_r = C_min/C_max
                                NTU = UA_tot[N_element*N_turn-1-N_element*tt-jj,rr]/C_min
                                
                                if C_min == c_primary*primary_in.m:
                                    eps[N_element*N_turn-1-N_element*tt-jj,rr] = 1-np.exp(-(1-np.exp(-NTU*C_r))/C_r)
                                else:
                                    eps[N_element*N_turn-1-N_element*tt-jj,rr] = (1-np.exp(-C_r*(1-np.exp(-NTU))))/C_r
                                    
                            Q_trans[N_element*N_turn-1-N_element*tt-jj,rr] = eps[N_element*N_turn-1-N_element*tt-jj,rr]*C_min*((T_primary[N_element*N_turn-1-N_element*tt-jj,rr] - T_secondary[N_element*N_turn-1-N_element*tt-jj,rr-1]))
                            
                            T_secondary[N_element*N_turn-1-N_element*tt-jj,rr] = T_secondary[N_element*N_turn-1-N_element*tt-jj,rr-1] + Q_trans[N_element*N_turn-1-N_element*tt-jj,rr]/(c_sec*mdot_sec/N_element/N_turn)
                            
                            if jj == N_element-1:
                                T_primary_in = T_primary[N_element*N_turn-1-N_element*tt-jj,rr]
                                h_primary_in = h_primary[N_element*N_turn-1-N_element*tt-jj,rr]
                                p_primary_in = p_primary[N_element*N_turn-1-N_element*tt-jj,rr]
                                x_primary_in = (h_primary_in-hl_primary)/(hg_primary - hl_primary)
                                Q_trans_in = Q_trans[N_element*N_turn-1-N_element*tt-jj,rr]
                                dp_in = dp_primary
                                
                        elif round(rr/2) == rr/2 and rr != 0:
                            if jj == 0:
                                h_primary[N_element*tt+jj,rr] = h_primary_in - Q_trans_in/primary_in.m
                                p_primary[N_element*tt+jj,rr] = p_primary_in - dp_in
                            else:
                                h_primary[N_element*tt+jj,rr] = h_primary[N_element*tt+jj-1,rr] - Q_trans[N_element*tt+jj-1,rr]/primary_in.m
                                p_primary[N_element*tt+jj,rr] = p_primary[N_element*tt+jj-1,rr] - dp_primary
                                    
                            hl_primary = PropsSI('H','P',p_primary[N_element*tt+jj,rr],'Q',0.0, primary_in.Y)
                            hg_primary = PropsSI('H','P',p_primary[N_element*tt+jj,rr],'Q',1.0, primary_in.Y)
                            x_primary[N_element*tt+jj,rr] = (h_primary[N_element*tt+jj,rr]-hl_primary)/(hg_primary - hl_primary)
                            T_primary[N_element*tt+jj,rr] = PropsSI('T','H',h_primary[N_element*tt+jj,rr],'P',p_primary[N_element*tt+jj,rr],primary_in.Y)
                            dT = T_primary[N_element*tt+jj,rr]-T_secondary[N_element*tt+jj,rr-1]
                            
                            if x_primary[N_element*tt+jj,rr] > 0 and x_primary[N_element*tt+jj,rr] < 1:
                                dl_primary = PropsSI('D','P',p_primary[N_element*tt+jj,rr],'Q',0.0, primary_in.Y)
                                dg_primary = PropsSI('D','P',p_primary[N_element*tt+jj,rr],'Q',1.0, primary_in.Y)
                                d_primary[N_element*tt+jj,rr] = 1/(x_primary[N_element*tt+jj,rr]/dg_primary+(1-x_primary[N_element*tt+jj,rr])/dl_primary)
                            else:
                                d_primary[N_element*tt+jj,rr] = PropsSI('D','T',T_primary[N_element*tt+jj,rr],'P',p_primary[N_element*tt+jj,rr],primary_in.Y)
                                c_primary = PropsSI('C','T',T_primary[N_element*tt+jj,rr],'P',p_primary[N_element*tt+jj,rr],primary_in.Y)
                            
                            if cor == True:
                                aaa = 1
                            else:
                                UA_tot[N_element*tt+jj,rr] = UA_const
                                dp_primary = dp_const
                                    
                            if x_primary[N_element*tt+jj,rr] > 0 and x_primary[N_element*tt+jj,rr] < 1:
                                C_min = c_sec*mdot_sec
                                NTU = UA_tot[N_element*tt+jj,rr]/C_min
                                eps[N_element*tt+jj,rr] = 1 - np.exp(-NTU)
                            else:
                                C_min = min(c_primary*primary_in.m, c_sec*mdot_sec)
                                C_max = max(c_primary*primary_in.m, c_sec*mdot_sec)
                                C_r = C_min/C_max
                                NTU = UA_tot[N_element*tt+jj,rr]/C_min
                                
                                if C_min == c_primary*primary_in.m:
                                    eps[N_element*tt+jj,rr] = 1-np.exp(-(1-np.exp(-NTU*C_r))/C_r)
                                else:
                                    eps[N_element*tt+jj,rr] = (1-np.exp(-C_r*(1-np.exp(-NTU))))/C_r
                                    
                            Q_trans[N_element*tt+jj,rr] = eps[N_element*tt+jj,rr]*C_min*((T_primary[N_element*tt+jj,rr] - T_secondary[N_element*tt+jj,rr-1]))
                            
                            T_secondary[N_element*tt+jj,rr] = T_secondary[N_element*tt+jj,rr-1] + Q_trans[N_element*tt+jj,rr]/(c_sec*mdot_sec/N_element/N_turn)
                            
                            if jj == N_element-1:
                                T_primary_in = T_primary[N_element*tt+jj,rr]
                                h_primary_in = h_primary[N_element*tt+jj,rr]
                                p_primary_in = p_primary[N_element*tt+jj,rr]
                                x_primary_in = (h_primary_in-hl_primary)/(hg_primary - hl_primary)
                                Q_trans_in = Q_trans[N_element*tt+jj,rr]
                                dp_in = dp_primary
            T_secondary_cal = np.mean(T_secondary[:,-1])
                    
            if noHX == 0:
                err_T_sec = (secondary_out.T - T_secondary_cal)/secondary_out.T
                if err_T_sec > 0:
                    T_sec_lb = T_sec
                else:
                    T_sec_ub = T_sec
            elif noHX == 1:
                err_T_sec = 0.0
                secondary_out.T = T_secondary_cal
            else:
                err_T_sec = (secondary_out.T - T_secondary_cal)/secondary_out.T
                if err_T_sec > 0:
                    mdot_sec_lb = mdot_sec
                else:
                    mdot_sec_ub = mdot_sec
        
            if abs(err_T_sec) < 1.0e-3:
                a_FTHX = 0
            else:
                if noHX == 2:
                    if (mdot_sec_ub - mdot_sec_lb)/mdot_sec < 1.0e-3:
                        a_FTHX = 0
                else:
                    if (T_sec_ub - T_sec_lb)/T_sec < 1.0e-3:
                        a_FTHX = 0
                        
        if err_index == 1:
            Q = 0.0
            mean_d = 0.0
            T_pp = 0.0
        else:
            mean_d = d_primary.mean()
            
            if round(N_row/2) == N_row/2:
                primary_out.T = T_primary[0,-1].item()
                primary_out.p = p_primary[0,-1].item()
                primary_out.h = h_primary[0,-1].item()
            else:
                primary_out.T = T_primary[-1,-1].item()
                primary_out.p = p_primary[-1,-1].item()
                primary_out.h = h_primary[-1,-1].item()
                
            try:
                primary_out.Ts=PropsSI('T','P',primary_out.p,'Q',0.5,primary_out.Y)
            except:
                primary_out.Ts = primary_out.T

            primary_out.hl=hl_primary
            primary_out.hg=hg_primary
            
            secondary_out.T = T_secondary_cal.item()
            
            if noHX == 1:
                secondary_in.T = T_sec
            elif noHX == 2:        
                secondary_in.m = mdot_sec
                secondary_out.m = mdot_sec
            
            Q1 = (primary_out.h - primary_in.h)*primary_in.m
            Q2 = Q_trans.sum()
            Q = min([Q1, Q2])
            T_pp = [abs(T1-T2) for T1, T2 in zip(T_primary, T_secondary)]
            T_pp = np.min(T_pp)
        return(primary_in, primary_out, secondary_in, secondary_out, Q, mean_d, T_pp, err_index)
            
if __name__ == '__main__':
    from HP_dataclass import*
    inputs = PHX_Inputs()
    inputs.thk_tot = 0.411
    inputs.thk_plate = 0.6e-3
    inputs.beta = 60
    inputs.L_width = 0.6
    inputs.L_vert = 0.8
    inputs.N_plate = 187
    inputs.cor_pitch = 0.002
    inputs.UA = 50000
    inputs.dp = 0.005
    inputs.mdot_nominal = 9.0
    
    
    noEvap = 2
    InEvap = Fluid_flow(Y='Water', m=0.0, T=280.15, p = 101300.0)
    OutEvap = Fluid_flow(Y='Water', m=0.0, T=278.15, p = 101300.0)
    if noEvap == 0:
        OutEvap.c = PropsSI("C","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.v = PropsSI("V","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.pr = PropsSI("Prandtl","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.l = PropsSI("L","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.d = PropsSI("D","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
    elif noEvap == 1:
        InEvap.c = PropsSI("C","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.v = PropsSI("V","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.pr = PropsSI("Prandtl","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.l = PropsSI("L","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.d = PropsSI("D","T",InEvap.T,"P",InEvap.p,InEvap.Y)       
    else:
        OutEvap.c = PropsSI("C","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.v = PropsSI("V","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.pr = PropsSI("Prandtl","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.l = PropsSI("L","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        OutEvap.d = PropsSI("D","T",OutEvap.T,"P",OutEvap.p,OutEvap.Y)
        InEvap.c = PropsSI("C","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.v = PropsSI("V","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.pr = PropsSI("Prandtl","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.l = PropsSI("L","T",InEvap.T,"P",InEvap.p,InEvap.Y)
        InEvap.d = PropsSI("D","T",InEvap.T,"P",InEvap.p,InEvap.Y)       
    
    InEvap_REF = Fluid_flow(Y='R410A')
    OutEvap_REF = Fluid_flow(Y='R410A', m=0.8, T=275.15, p = 0.7e6)
    OutEvap_REF.h = PropsSI(OutEvap_REF, 'H','T','P')
    OutEvap_REF.hl = PropsSI('H','P',OutEvap_REF.p,'Q',0.0, OutEvap_REF.Y )
    OutEvap_REF.hg = PropsSI('H','P',OutEvap_REF.p,'Q',1.0, OutEvap_REF.Y )
    Evap = HX_module(hx_type='phx',  cor=False, Inputs=inputs)
    (OutEvap_REF, OutEvap_REF, InEvap, OutEvap, Q, mean_d)=Evap.PHX('evap', OutEvap_REF, OutEvap_REF, InEvap, OutEvap, noEvap)
    