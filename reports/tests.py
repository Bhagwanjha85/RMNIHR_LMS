from django.test import TestCase, Client
from django.contrib.auth.models import User
from reports.models import Report, ReportTest
from django.urls import reverse

class ReportTestModelTests(TestCase):
    def setUp(self):
        self.report = Report.objects.create(
            lab_id="9999",
            patient_name="TEST PATIENT",
            age_value=30,
            age_unit="Y",
            sex="M",
            test_method="ELISA",
            sample_type="BLOOD",
            receiving_date="2026-06-25",
            reporting_date="2026-06-25",
            ref_by="TEST LAB"
        )

    def test_standard_elisa_cutoffs(self):
        t1 = ReportTest.objects.create(report=self.report, test_name="Dengue IgM", result_value="5.0")
        t2 = ReportTest.objects.create(report=self.report, test_name="Dengue IgM", result_value="10.0")
        t3 = ReportTest.objects.create(report=self.report, test_name="Dengue IgM", result_value="12.0")
        
        self.assertEqual(t1.interpretation_text, "Negative")
        self.assertEqual(t2.interpretation_text, "Equivocal")
        self.assertEqual(t3.interpretation_text, "Positive")
        self.assertEqual(t1.interpretation_range, "Negative &lt; 9.00 | Equivocal 9.00-11.00 | Positive &gt; 11.00")

    def test_hbsag_elisa_cutoffs(self):
        t1 = ReportTest.objects.create(report=self.report, test_name="HBsAg", result_value="0.100")
        t2 = ReportTest.objects.create(report=self.report, test_name="HBsAg", result_value="0.191")
        t3 = ReportTest.objects.create(report=self.report, test_name="HBsAg", result_value="0.250")
        
        self.assertEqual(t1.interpretation_text, "Non-Reactive")
        self.assertEqual(t2.interpretation_text, "Reactive")
        self.assertEqual(t3.interpretation_text, "Reactive")
        self.assertEqual(t1.interpretation_range, "Non-Reactive &lt; 0.191 | Reactive &ge; 0.191")

    def test_hcv_antibody_elisa_cutoffs(self):
        t1 = ReportTest.objects.create(report=self.report, test_name="HCV Antibody", result_value="0.300")
        t2 = ReportTest.objects.create(report=self.report, test_name="HCV Antibody", result_value="0.361")
        t3 = ReportTest.objects.create(report=self.report, test_name="HCV Antibody", result_value="0.450")
        
        self.assertEqual(t1.interpretation_text, "Non-Reactive")
        self.assertEqual(t2.interpretation_text, "Reactive")
        self.assertEqual(t3.interpretation_text, "Reactive")
        self.assertEqual(t1.interpretation_range, "Non-Reactive &lt; 0.361 | Reactive &ge; 0.361")

class LoginGeofencingTests(TestCase):
    def setUp(self):
        self.username = "admin"
        self.password = "password123"
        self.user = User.objects.create_superuser(
            username=self.username,
            password=self.password,
            email="admin@test.com"
        )
        self.client = Client()

    def test_login_without_geofencing(self):
        # Post to login page without latitude/longitude parameters should succeed
        login_url = reverse('login')
        response = self.client.post(login_url, {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302) # Redirect to dashboard
        self.assertRedirects(response, reverse('dashboard'))

