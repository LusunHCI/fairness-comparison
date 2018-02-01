from algorithms.Algorithm import Algorithm
import numpy
import tempfile
import os
import subprocess

class CaldersAlgorithm(Algorithm):
    """
    Notes:

    - The original code depends on python2's commands library. We hacked
    it to have python3 support by adding a minimal commands.py module with
    a getoutput function.

    """

    def __init__(self):
        Algorithm.__init__(self)
        self.name = "Calders"

    def run(self, train_df, test_df, class_attr, positive_class_val, sensitive_attrs,
            single_sensitive, privileged_vals, params):

        if not 'beta' in params:
            params = self.get_default_params()

        value_0 = train_df[class_attr].values[0]
        if type(value_0) == str:
            class_type = str
        else:
            class_type = type(value_0.item()) # this should be numpy.int64 or numpy.int32,

        def create_file_in_kamishima_format(df):
            y = df[class_attr]
            s = df[single_sensitive]

            x = []
            for col in df:
                if col == class_attr:
                    continue
                if col in sensitive_attrs:
                    continue
                x.append(numpy.array(df[col].values, dtype=numpy.float64))

            x.append(numpy.array(s, dtype=numpy.float64))
            x.append(numpy.array(df[class_attr], dtype=numpy.float64))

            result = numpy.array(x).T
            fd, name = tempfile.mkstemp()
            os.close(fd)
            numpy.savetxt(name, result)
            return name
        
        train_col_sets = list(set(train_df[col]) for col in train_df
                              if col not in sensitive_attrs + [class_attr])
        test_col_sets = list(set(test_df[col]) for col in test_df
                             if col not in sensitive_attrs + [class_attr])
        nfv = ":".join(str(len(a.union(b))) for (a,b) in zip(train_col_sets, test_col_sets))

        fd, model_name = tempfile.mkstemp()
        os.close(fd)
        fd, output_name = tempfile.mkstemp()
        os.close(fd)
        train_name = create_file_in_kamishima_format(train_df)
        test_name = create_file_in_kamishima_format(test_df)
        beta_val = params['beta']
        subprocess.run(['python3', './algorithms/kamishima/kamfadm-2012ecmlpkdd/train_cv2nb.py',
                        '-b', str(beta_val),
                        '-f', nfv,
                        '-i', train_name,
                        '-o', model_name,
                        '--quiet'])
        subprocess.run(['python3', './algorithms/kamishima/kamfadm-2012ecmlpkdd/predict_nb.py',
                        '-i', test_name,
                        '-m', model_name,
                        '-o', output_name,
                        '--quiet'])
        os.unlink(train_name)
        os.unlink(model_name)
        os.unlink(test_name)

        m = numpy.loadtxt(output_name)
        os.unlink(output_name)

        predictions = m[:,1]
        predictions_correct = [class_type(x) for x in predictions]

        return predictions_correct

    def get_supported_data_types(self):
        return set(["numerical-binsensitive"])

    def get_default_params(self):
        """
        According to the source code, 
        'coefficient of a prior for feature probabilities (default 1.0)'
        """
        return { 'beta' : 1.0 }

    def get_param_info(self):
        """
        FIXME this is probably completely wrong.
        """
        return {'beta' : [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]}


