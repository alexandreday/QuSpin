from .base import basis,MAXPRINT
from .tensor import tensor_basis

import numpy as _np
from scipy import sparse as _sp

from scipy.special import hyp2f1, binom

import warnings


def coherent_state(a,n,dtype=_np.float64):
	"""
	This function creates a harmonic oscillator coherent state.

	RETURNS: numpy array with harmonic oscilaltor coherent state.

	--- arguments ---

	a: (required) expectation value of annihilation operator, i.e. sqrt(mean particle number)

	n: (required) cut-off on the number of states kept in the definition of the coherent state

	dtype: (optional) data type. Default is set to numpy.float64
	"""

	s1 = _np.full((n,),-_np.abs(a)**2/2.0,dtype=dtype)
	s2 = _np.arange(n,dtype=_np.float64)
	s3 = _np.array(s2)
	s3[0] = 1
	_np.log(s3,out=s3)
	s3[1:] = 0.5*_np.cumsum(s3[1:])
	state = s1+_np.log(a)*s2-s3
	return _np.exp(state)

def photon_Hspace_dim(N,Ntot,Nph):
	"""
	This function calculates the dimension of the total spin-photon Hilbert space.
	"""
	if Ntot is None and Nph is not None: # no total particle # conservation
		return 2**N*(Nph+1)
	elif Ntot is not None:
		return 2**N - binom(N,Ntot+1)*hyp2f1(1,1-N+Ntot,2+Ntot,-1)
	else:
		raise TypeError("Either 'Ntot' or 'Nph' must be defined!")

	

class photon_basis(tensor_basis):
	def __init__(self,basis_constructor,*constructor_args,**blocks):
		Ntot = blocks.get("Ntot")
		Nph = blocks.get("Nph")
		self.Nph = Nph
		self.Ntot = Ntot
		if Ntot is not None: blocks.pop("Ntot")
		if Nph is not None: blocks.pop("Nph")

		if Ntot is None:
			if Nph is None: raise TypeError("If Ntot not specified, Nph must specify the cutoff on the number of photon states.")
			if type(Nph) is not int: raise TypeError("Nph must be integer")
			if Nph < 0: raise ValueError("Nph must be an integer >= 0.")

			self._check_pcon=False
			b1 = basis_constructor(*constructor_args,_Np=-1,**blocks)
			b2 = ho_basis(Nph)
			tensor_basis.__init__(self,b1,b2)
		else:
			if type(Ntot) is not int: raise TypeError("Ntot must be integer")
			if Ntot < 0: raise ValueError("Ntot must be an integer >= 0.")

			self._check_pcon=True
			self._b1 = basis_constructor(*constructor_args,_Np=Ntot,**blocks)
			if isinstance(self._b1,tensor_basis): raise TypeError("Can only create photon basis with non-tensor type basis")
			if not isinstance(self._b1,basis): raise TypeError("Can only create photon basis with basis type")
			self._b2 = ho_basis(Ntot)
			self._n = Ntot - self._b1._Np 
			self._blocks = self._b1._blocks
			self._Ns = self._b1._Ns
			self._unique_me = self._b1.unique_me
			self._operators = self._b1._operators +"\n"+ self._b2._operators
			


	def Op(self,opstr,indx,J,dtype):
		if self._Ns <= 0:
			return [],[],[]

		opstr1,opstr2=opstr.split("|")

		if len(opstr1) != len(indx):
			raise ValueError("The length of indx must be the same length as particle operators in {0},{1}".format(opstr,indx))


		if not self._check_pcon:
			n = len(opstr.replace("|","")) - len(indx)
			indx.extend([0 for i in range(n)])

			return tensor_basis.Op(self,opstr,indx,J,dtype)
		else:
			# read off spin and photon operators
			n = len(opstr.replace("|","")) - len(indx)
			indx.extend([0 for i in range(n)])

			if opstr.count("|") > 1: 
				raise ValueError("only one '|' charactor allowed in opstr {0}".format(opstr))
			if len(opstr)-1 != len(indx):
				raise ValueError("not enough indices for opstr in: {0}, {1}".format(opstr,indx))

			i = opstr.index("|")
			indx1 = indx[:i]
			indx2 = indx[i:]			

			opstr1,opstr2=opstr.split("|")

			# calculates matrix elements of spin and photon basis
			# the coupling 1.0 in self._b2.Op is used in order not to square the coupling J
			ME_ph,row_ph,col_ph =  self._b2.Op(opstr2,indx2,1.0,dtype)
			ME, row, col  =	self._b1.Op(opstr1,indx1,J,dtype)

			# calculate total matrix element
			ME *= ME_ph[self._n[col]]

			mask = ME != dtype(0.0)
			row = row[mask]
			col = col[mask]
			ME = ME[mask]

			del ME_ph, row_ph, col_ph

			return ME, row, col	


	def get_vec(self,v0,sparse=True,Nph=None,full_part=True):
		if not self._check_pcon:
			return tensor_basis.get_vec(self,v0,sparse=sparse,full_1=full_part)
		else:
			if Nph is None:
				Nph = self.Ntot

			if not type(Nph) is int:
				raise TypeError("Nph must be integer")

			if Nph < self.Ntot:
				raise ValueError("Nph must be larger or equal to {0}".format(self.Ntot))
		
			if v0.ndim == 1:
				if v0.shape[0] != self._Ns:
					raise ValueError("v0 has incompatible dimensions with basis")
				v0 = v0.reshape((-1,1))
				if sparse:
					return _conserved_get_vec(self,v0,sparse,Nph,full_part)
				else:
					return _conserved_get_vec(self,v0,sparse,Nph,full_part).reshape((-1,))

			elif v0.ndim == 2:
				if v0.shape[0] != self._Ns:
					raise ValueError("v0 has incompatible dimensions with basis")

				return _conserved_get_vec(self,v0,sparse,Nph,full_part)
			else:
				raise ValueError("excpecting v0 to have ndim at most 2")




	def get_proj(self,dtype,Nph=None,full_part=True):
		if not self._check_pcon:
			return tensor_basis.get_proj(self,dtype,full_1=full_part)	
		else:
			if Nph is None:
				Nph = self.Ntot

			if not type(Nph) is int:
				raise TypeError("Nph must be integer")

			if Nph < self.Ntot:
				raise ValueError("Nph must be larger or equal to {0}".format(self.Ntot))

#			raise NotImplementedError("get_proj not implimented for particle conservation symm.")
			# still needs testing...
			return _conserved_get_proj(self,dtype,Nph,full_part)


	@property
	def chain_Ns(self):
		return self._b1.Ns

	@property
	def chain_N(self):
		return self._b1.N
	
	

	def __name__(self):
		return "<type 'qspin.basis.photon_basis'>"

	def _get__str__(self):
		if not self._check_pcon:
			return tensor_basis._get__str__(self)
		else:
			if not hasattr(self._b1,"_get__str__"):
				warnings.warn("basis class {0} missing _get__str__ function, can not print out basis representatives.".format(type(self._b1)),UserWarning,stacklevel=3)
				return "reference states: \n\t not availible"

			n_digits = int(_np.ceil(_np.log10(self._Ns)))

			str_list_1 = self._b1._get__str__()
			temp = "\t{0:"+str(n_digits)+"d}.  "
			str_list=[]
			for b1 in str_list_1:
				b1 = b1.replace(".","")
				b1 = b1.split()
				s1 = b1[1]
				i1 = int(b1[0])
				s2 = "|{0}>".format(self._n[i1])
				str_list.append((temp.format(i1))+"\t"+s1+s2)

			if self._Ns > MAXPRINT:
				half = MAXPRINT//2
				str_list_1 = str_list[:half]
				str_list_2 = str_list[-half:]

				str_list = str_list_1
				str_list.extend(str_list_2)	

			return str_list	


	def _sort_opstr(self,op):
		op = list(op)
		opstr = op[0]
		indx  = op[1]

		if opstr.count("|") == 0: 
			raise ValueError("missing '|' charactor in: {0}, {1}".format(opstr,indx))
	
		if opstr.count("|") > 1: 
			raise ValueError("only one '|' charactor allowed in: {0}, {1}".format(opstr,indx))

		if len(opstr)-1 != len(indx):
			raise ValueError("number of indices doesn't match opstr in: {0}, {1}".format(opstr,indx))

		i = opstr.index("|")
		indx1 = indx[:i]
		indx2 = indx[i:]

		opstr1,opstr2=opstr.split("|")

		op1 = list(op)
		op1[0] = opstr1
		op1[1] = tuple(indx1)

		if indx1: ind_min = min(indx1)
		else: ind_min = 0


		op2 = list(op)
		op2[0] = opstr2
		op2[1] = tuple([ind_min for i in opstr2])
		
		op1 = self._b1.sort_opstr(op1)
		op2 = self._b2.sort_opstr(op2)

		op[0] = "|".join((op1[0],op2[0]))
		op[1] = op1[1] + op2[1]
		
		return tuple(op)

	def _check_symm(self,static,dynamic):
		# pick out operators which have charactors to the left of the '|' charactor. 
		# otherwise this is operator must be
		new_static = []
		for opstr,bonds in static:
			if opstr.count("|") == 0: 
				raise ValueError("missing '|' character in: {0}".format(opstr))

			opstr1,opstr2=opstr.split("|")

			if opstr1:
				new_static.append([opstr,bonds])


		new_dynamic = []
		for opstr,bonds,f,f_args in dynamic:
			if opstr.count("|") == 0: 
				raise ValueError("missing '|' character in: {0}".format(opstr))

			opstr1,opstr2=opstr.split("|")

			if opstr1:
				new_dynamic.append([opstr,bonds,f,f_args])
		
		return self._b1._check_symm(new_static,new_dynamic,basis=self)



	def _get_lists(self,static,dynamic): #overwrite the default get_lists from base.
		static_list = []
		for opstr,bonds in static:
			if opstr.count("|") == 0: 
				raise ValueError("missing '|' character in: {0}".format(opstr))

			opstr1,opstr2=opstr.split("|")

			for bond in bonds:
				indx = list(bond[1:])

				if len(opstr1) != len(indx):
					raise ValueError("The length of indx must be the same length as particle operators in {0},{1}".format(opstr,indx))

				# extend the operators such that the photon ops get an index.
				# choose that the index is equal to the smallest indx of the spin operators
				n = len(opstr.replace("|","")) - len(indx)

				if opstr1:
					indx.extend([min(indx) for i in range(n)])
				else:
					indx.extend([0 for i in range(n)])

				J = complex(bond[0])
				static_list.append((opstr,tuple(indx),J))

		dynamic_list = []
		for opstr,bonds,f,f_args in dynamic:
			if opstr.count("|") == 0: 
				raise ValueError("missing '|' character in: {0}".format(opstr))

			opstr1,opstr2=opstr.split("|")

			for bond in bonds:
				indx = list(bond[1:])

				if len(opstr1) != len(indx):
					raise ValueError("The length of indx must be the same length as particle operators in {0},{1}".format(opstr,indx))

				# extend the operators such that the photon ops get an index.
				# choose that the index is equal to the smallest indx of the spin operators
				n = len(opstr.replace("|","")) - len(indx)

				if opstr1:
					indx.extend([min(indx) for i in range(n)])
				else:
					indx.extend([0 for i in range(n)])

				J = complex(bond[0])
				dynamic_list.append((opstr,tuple(indx),J,f,f_args))

		return tensor_basis.sort_list(self,static_list),tensor_basis.sort_list(self,dynamic_list)




				








def _conserved_get_vec(p_basis,v0,sparse,Nph,full_part):
	v0_mask = _np.zeros_like(v0)
	np_min = p_basis._n.min()
	np_max = p_basis._n.max()
	v_ph = _np.zeros((Nph+1,1),dtype=_np.int8)
	
	v_ph[np_min] = 1
	mask = p_basis._n == np_min
	v0_mask[mask] = v0[mask]

	if full_part:
		v0_full = p_basis._b1.get_vec(v0_mask,sparse=sparse)
	else:
		v0_full = v0_mask

	if sparse:
		v0_full = _sp.kron(v0_full,v_ph,format="csr")
	else:
		v0_full = _np.kron(v0_full,v_ph)
		
	v_ph[np_min] = 0
	v0_mask[mask] = 0.0

	for np in range(np_min+1,np_max+1,1):
		v_ph[np] = 1
		mask = p_basis._n == np
		v0_mask[mask] = v0[mask]

		if full_part:
			v0_full_1 = p_basis._b1.get_vec(v0_mask,sparse=sparse)
		else:
			v0_full_1 = v0_mask

		if sparse:
			v0_full = v0_full + _sp.kron(v0_full_1,v_ph,format="csr")
			v0_full.sum_duplicates()
			v0_full.eliminate_zeros()
		else:
			v0_full += _np.kron(v0_full_1,v_ph)
		
		v_ph[np] = 0
		v0_mask[mask] = 0.0		



	return v0_full




def _conserved_get_proj(p_basis,dtype,Nph,full_part):
	np_min = p_basis._n.min()
	np_max = p_basis._n.max()
	v_ph = _np.zeros((Nph+1,1),dtype=_np.int8)

	if full_part:
		proj_1 = p_basis._b1.get_proj(dtype)
	else:
		proj_1 = _sp.identity(p_basis.Ns,dtype=dtype,format="csr")

	proj_1_mask = _sp.lil_matrix(proj_1.shape,dtype=dtype)


	v_ph[np_min] = 1
	mask = p_basis._n == np_min
	proj_1_mask[:,mask] = proj_1[:,mask]

	proj_1_full = _sp.kron(proj_1_mask,v_ph,format="csr")

	proj_1_mask[:,:]=0.0
	v_ph[np_min] = 0


	for np in range(np_min+1,np_max+1,1):
		v_ph[np] = 1
		mask = p_basis._n == np
		proj_1_mask[:,mask] = proj_1[:,mask]

		proj_1_full = proj_1_full + _sp.kron(proj_1_mask,v_ph,format="csr")

		proj_1_mask[:,:]=0.0
		v_ph[np] = 0		




	return proj_1_full



# helper class which calcualates ho matrix elements
class ho_basis(basis):
	def __init__(self,Np):
		if (type(Np) is not int):
			raise ValueError("expecting integer for Np")

		self._Np = Np
		self._Ns = Np+1
		self._dtype = _np.min_scalar_type(-self.Ns)
		self._basis = _np.arange(self.Ns,dtype=_np.min_scalar_type(self.Ns))
		self._operators = ("availible operators for ho_basis:"+
							"\n\tI: identity "+
							"\n\t+: raising operator"+
							"\n\t-: lowering operator"+
							"\n\tn: number operator")

		self._blocks = {}

	@property
	def Np(self):
		return self._Np

	def get_vec(self,v0,sparse=True):
		if self._Ns <= 0:
			return _np.array([])
		if v0.ndim == 1:
			if v0.shape[0] != self.Ns:
				raise ValueError("v0 has incompatible dimensions with basis")
			v0 = v0.reshape((-1,1))
		elif v0.ndim == 2:
			if v0.shape[0] != self.Ns:
				raise ValueError("v0 has incompatible dimensions with basis")
		else:
			raise ValueError("excpecting v0 to have ndim at most 2")

		if sparse:
			return _sp.csr_matrix(v0)
		else:
			return v0

	def __getitem__(self,key):
		return self._basis.__getitem__(key)

	def index(self,s):
		return _np.searchsorted(self._basis,s)

	def __iter__(self):
		return self._basis.__iter__()

	def _get__str__(self):
		n_digits = int(_np.ceil(_np.log10(self._Ns)))
		temp = "\t{0:"+str(n_digits)+"d}.  "+"|{1}>"

		if self._Ns > MAXPRINT:
			half = MAXPRINT // 2
			str_list = [temp.format(i,b) for i,b in zip(range(half),self._basis[:half])]
			str_list.extend([temp.format(i,b) for i,b in zip(range(self._Ns-half,self._Ns,1),self._basis[-half:])])
		else:
			str_list = [temp.format(i,b) for i,b in enumerate(self._basis)]

		return str_list

		
	def _sort_opstr(self,op):
		return tuple(op)


	def _hc_opstr(self,op):
		op = list(op)
		op[0] = list(op[0].replace("+","%").replace("-","+").replace("%","-"))
		op[0].reverse()
		op[0] = "".join(op[0])

		op[1] = list(op[1])
		op[1].reverse()
		op[1] = tuple(op[1])

		op[2] = op[2].conjugate()
		return self._sort_opstr(op)


	def _non_zero(self,op):
		m = (op[0].count("-") > self._Np)
		p = (op[0].count("+") > self._Np)
		return (p or m)


	def _expand_opstr(self,op,num):
		op = list(op)
		op.append(num)
		op = tuple(op)
		return tuple([op])


	def get_proj(self,dtype):
		return _sp.identity(self.Ns,dtype=dtype)


	def Op(self,opstr,indx,J,dtype,*args):

		row = _np.array(self._basis,dtype=self._dtype)
		col = _np.array(self._basis,dtype=self._dtype)
		ME = _np.ones((self._Ns,),dtype=dtype)


		if len(opstr) != len(indx):
			raise ValueError('length of opstr does not match length of indx')
		if not _np.can_cast(J,_np.dtype(dtype)):
			raise TypeError("can't cast J to proper dtype")

		for o in opstr[::-1]:
			if o == "I":
				continue
			elif o == "n":
				ME *= dtype(_np.abs(row))
			elif o == "+":
				row += 1
				ME *= _np.sqrt(dtype(_np.abs(row)))
			elif o == "-":
				ME *= _np.sqrt(dtype(_np.abs(row)))
				row -= 1
			else:
				raise Exception("operator symbol {0} not recognized".format(o))

		mask = ( row < 0)
		mask += (row >= (self._Ns))
		row[mask] = col[mask]
		ME[mask] = 0.0

		
		if J != 1.0: 
			ME *= J

		return ME,row,col		
		
