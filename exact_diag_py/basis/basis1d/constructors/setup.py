








def get_templates(folder,ext):
	import os,glob
	package_dir = os.path.dirname(os.path.realpath(__file__))
	sources_dir = os.path.join(*([package_dir]+folder))
	sources=glob.glob(os.path.join(sources_dir,"*"+ext))


	return sources





def basis_ops_gen():
	basis_types = [
					{"np_basis_type":"NP_UINT32","c_basis_type":"unsigned int"},
				]

	matrix_types = [
									{"type_code":"s","c_matrix_type":"float","np_matrix_type":"NP_FLOAT32","c_complex_type":"float complex","c_float_type":"float","check_imag":"True"},
									{"type_code":"d","c_matrix_type":"double","np_matrix_type":"NP_FLOAT64","c_complex_type":"double complex","c_float_type":"double","check_imag":"True"},
									{"type_code":"c","c_matrix_type":"float complex","np_matrix_type":"NP_COMPLEX64","c_complex_type":"float complex","c_float_type":"float","check_imag":"False"},
									{"type_code":"z","c_matrix_type":"double complex","np_matrix_type":"NP_COMPLEX128","c_complex_type":"double complex","c_float_type":"double","check_imag":"False"},
								]

	op_templates = get_templates(['sources','op'],".tmp")


	for op_template in op_templates:
		IO = open(op_template,"r")
		filename = op_template.replace(".tmp","")
		file_temp_str = IO.read()
		print filename
		replacements = []
		for basis_type in basis_types:
			for matrix_type in matrix_types:
				replace = basis_type.copy()	
				replace.update(matrix_type)
				replacements.append(replace)


		file_str = ""
		for replace in replacements:

			try:
				file_str += file_temp_str.format(**replace)
			except KeyError,e:
				print filename,replace
				raise KeyError(e)
			

		with open(filename,"w") as IO:
			IO.write(file_str)



	basis_templates = get_templates(['sources','basis'],".tmp")
	basis_templates += get_templates(['sources'],".tmp")


	for basis_template in basis_templates:
		IO = open(basis_template,"r")
		filename = basis_template.replace(".tmp","")
		print filename
		file_temp_str = IO.read()

		file_str = ""
		for replace in basis_types:
			try:
				file_str += file_temp_str.format(**replace)
			except KeyError,e:
				print filename,replace
				raise KeyError(e)

			

		with open(filename,"w") as IO:
			IO.write(file_str)







def cython_files():
	import os
	try:
		import Cython
		USE_CYTHON = True
	except ImportError:
		USE_CYTHON = False

	package_dir = os.path.dirname(os.path.realpath(__file__))


	if USE_CYTHON:
		print "generating .pyx files"
		basis_ops_gen()
		print "cythonizing basis_ops.pyx"
		cython_src =  os.path.join(package_dir,"basis_ops.pyx")
		os.system("cython --cplus "+cython_src)


	return  os.path.join(package_dir,"basis_ops.cpp")
		



def configuration(parent_package='', top_path=None):
		import numpy
		from numpy.distutils.misc_util import Configuration
		config = Configuration('constructors',parent_package, top_path)
		config.add_extension('basis_ops',sources=cython_files(),include_dirs=[numpy.get_include()],language="c++")
		return config

if __name__ == '__main__':
		from numpy.distutils.core import setup
		import sys
		try:
			instr = sys.argv[1]
			if instr == "build_templates":
				cython_files()
			else:
				setup(**configuration(top_path='').todict())
		except IndexError: pass





