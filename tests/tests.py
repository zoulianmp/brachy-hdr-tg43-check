from context import *
import dicom
import unittest


class BasicTestSetupClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup to run before all tests"""
        with open(r'tests\\tests_config.cfg', 'r') as f:
            d = f.read()
        test_config = {k: v for k, v in [x.split('=') for x in d.split('\n')]}
        cls.patient_id_test = test_config['patient_id']
        cls.case_name_test = test_config['case_name']
        cls.plan_name_test = test_config['plan_name']

        output_full_path = r'tests\\data\\rtplan.dcm'

        # output_full_path
        rt_plan_blob = get_rtplan(cls.patient_id_test,
                                  cls.case_name_test,
                                  cls.plan_name_test)  # return RTplan as BLOB

        write_file(rt_plan_blob[0][1], output_full_path)  # save BLOB to dcm
        ds_input = dicom.read_file(output_full_path)  # read in dcm

       # ds_input = dicom.read_file(r'tests\\data\\test_data.dcm')  # read in dcm
        cls.my_plan = BrachyPlan(ds_input)


class FirstTests(BasicTestSetupClass):
    @classmethod
    def setUpClass(cls):
        """Setup to run just for these tests"""
        super(FirstTests, cls).setUpClass()

    def test_exists_plan(self):
        """Test that RTPlan can be opened"""
        self.assertTrue(self.my_plan)

    def test_patient_demogs(self):
        """Test patient demographics"""
        self.assertTrue(self.my_plan.patient_id, self.patient_id_test)
        self.assertTrue(self.my_plan.plan_name, self.plan_name_test)


class SourceTests(BasicTestSetupClass):
    @classmethod
    def setUpClass(cls):
        """Setup to run just for these tests"""
        super(SourceTests, cls).setUpClass()
        cls.my_source_train = make_source_trains(cls.my_plan)
        cls.points_of_interest = cls.my_plan.points
        cls.poi_in = cls.points_of_interest[0]
        cls.my_point = PointPosition(
            cls.poi_in.coords[0] / 10,  # lateral
            cls.poi_in.coords[2] / 10,  # sup-inf
            cls.poi_in.coords[1] / 10)  # ant-post

    def test_source_train(self):
        """Test length of source train"""
        self.assertTrue(len(self.my_source_train), 2)

    def test_poi_location(self):
        """Test location of POI"""
        self.assertTrue(self.points_of_interest[0].coords, [-26.263365, -6.806701, -94.109772])

    def test_dwell_times(self):
        """Test dwell times"""
        self.assertTrue(self.my_source_train[0].dwellTime, 33.72160035605183)

    def test_channel_numbers(self):
        """Test channel numbers"""
        self.assertTrue(self.my_plan.channel_numbers, [1, 3])

    def test_prescription(self):
        """Test value of prescription dose"""
        self.assertTrue(self.my_plan.prescription, 7.1)

    def test_radial_dose_function(self):
        """Test radial dose value"""
        radial_dose = make_radial_dose(
            read_file(r'hdrpackage\\source_files\\v2r_ESTRO_radialDose.csv'))
        self.assertTrue(radialDose.gL[0], 1.3732)

        radial_dose_val = get_radial_dose(
            radial_dose, self.my_source_train[0], self.my_point)
        self.assertTrue(radial_dose_val,  1.00710588)

    def test_anisotropy_function(self):
        """Test anisotropy function value"""
        anisotropy_function = make_radial_dose(
            read_file(r'hdrpackage\\source_files\\v2r_ESTRO_radialDose.csv'))
        self.assertTrue(radialDose.gL[0], 1.3732)

        radial_dose_val = get_radial_dose(
            radialDose, self.my_source_train[0], self.my_point)
        self.assertTrue(radial_dose_val, 1.00710588)

    def test_geometry_function(self):
        """Test geometry function"""
        my_geometry_function = get_geometry_function(
            self.my_source_train[0], self.my_point)
        self.assertTrue(my_geometry_function, 0.13573403)


class DoseTests(BasicTestSetupClass):
    @classmethod
    def setUpClass(cls):
        """Setup to run just for these tests"""
        super(DoseTests, cls).setUpClass()
        cls.my_source_train = make_source_trains(cls.my_plan)
        cls.points_of_interest = cls.my_plan.points

    def test_dose_calculation(self):
        output_table = []

        for poi in self.points_of_interest:  # for each point
            my_dose = calculate_dose(self.my_source_train, poi)  # calculate dose
            point_compare = PointComparison(point_name=poi.name,  # and compare to OMP
                                            omp_dose=poi.dose,
                                            pytg43_dose=my_dose)
            output_table.append([poi.name,  # display as pretty table
                                poi.dose,
                                my_dose,
                                point_compare.percentage_difference])

        comparison_table = [['A1', 7.157785, 7.204668479752138, -0.650737502827492],
                            ['A2', 7.042215, 7.0942845357605915, -0.7339645808977835],
                            ['Bladder', 3.872681, 4.09607914018399, -5.453950779231176],
                            ['ICRU', 3.510379, 3.364742911392422, 4.32829765728846]]

        self.assertTrue(output_table, comparison_table)

if __name__ == '__main__':
    unittest.main()
