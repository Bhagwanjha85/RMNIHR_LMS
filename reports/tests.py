from django.test import TestCase, Client
from django.contrib.auth.models import User
from reports.models import Report, ReportTest, TestConfig, UserProfile
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

    def test_qualitative_interpretation_preservation(self):
        config = TestConfig.objects.create(
            test_name="Zika Virus IgM",
            test_method="ELISA",
            result_type="select"
        )
        t = ReportTest.objects.create(
            report=self.report,
            test_name="Zika Virus IgM",
            result_value="-",
            interpretation_text="Positive",
            test_method="ELISA"
        )
        self.assertEqual(t.interpretation_text, "Positive")

    def test_reactive_non_reactive_config(self):
        config = TestConfig.objects.create(
            test_name="HIV Screening",
            test_method="RAPID",
            result_type="reactive_non_reactive"
        )
        t = ReportTest.objects.create(
            report=self.report,
            test_name="HIV Screening",
            result_value="Reactive",
            test_method="RAPID"
        )
        self.assertEqual(t.interpretation_text, "Reactive")
        self.assertEqual(t.interpretation_range, "Reactive / Non-Reactive")

    def test_custom_dropdown_config(self):
        config = TestConfig.objects.create(
            test_name="Special Custom Test",
            test_method="ELISA",
            result_type="custom_dropdown",
            custom_options="Weak Positive, Strong Positive, Negative"
        )
        t = ReportTest.objects.create(
            report=self.report,
            test_name="Special Custom Test",
            result_value="Strong Positive",
            test_method="ELISA"
        )
        self.assertEqual(t.interpretation_text, "Strong Positive")
        self.assertEqual(t.interpretation_range, "Weak Positive / Strong Positive / Negative")

class LoginGeofencingTests(TestCase):
    def setUp(self):
        self.username = "admin"
        self.password = "password123"
        self.user = User.objects.create_superuser(
            username=self.username,
            password=self.password,
            email="admin@test.com"
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.is_admin_added_by_superadmin = True
        self.profile.save()
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


class SuperAdminPanelTests(TestCase):
    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            username="superadmin",
            password="password123",
            email="superadmin@test.com"
        )
        self.superadmin_profile, _ = UserProfile.objects.get_or_create(user=self.superadmin)
        self.superadmin_profile.is_super_admin = True
        self.superadmin_profile.save()
        
        # Create 15 test configs
        for i in range(15):
            TestConfig.objects.create(
                test_name=f"Test Config {i}",
                test_method="ELISA",
                result_type="numeric",
                cutoff_value=1.0
            )
            
        # Create 15 admins
        for i in range(15):
            u = User.objects.create_user(
                username=f"admin_user_{i}",
                password="password123",
                email=f"admin_{i}@test.com"
            )
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.is_admin_added_by_superadmin = True
            profile.save()
            
        self.client = Client()
        self.client.login(username="superadmin", password="password123")

    def test_super_admin_panel_pagination(self):
        # Default page 1
        response = self.client.get(reverse('super_admin_panel'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('configs', response.context)
        self.assertIn('added_admins', response.context)
        
        # Test pagination page sizes (should show 10 configs and 10 admins)
        self.assertEqual(len(response.context['configs'].object_list), 10)
        self.assertEqual(len(response.context['added_admins'].object_list), 10)
        
        # Page 2 of configs
        response = self.client.get(reverse('super_admin_panel') + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['configs'].object_list), 5)
        
        # Page 2 of admins
        response = self.client.get(reverse('super_admin_panel') + "?admin_page=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['added_admins'].object_list), 5)


class ReportPrintTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="rmnihr",
            password="rmnihr03072026",
            email="rmnihr@test.com"
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.is_super_admin = True
        self.profile.save()
        
        self.report = Report.objects.create(
            lab_id="1234",
            patient_name="John Doe",
            age_value=45,
            age_unit="Y",
            sex="M",
            test_method="ELISA",
            sample_type="BLOOD",
            receiving_date="2026-07-20",
            reporting_date="2026-07-20",
            ref_by="Referrer",
            show_prepared_by=True,
            show_technician=True,
            show_scientist=True,
            show_vc=True,
            prepared_by_name="Prep Agent",
            technician_name="Tech Agent",
            scientist_name="Scientist Agent",
            vc_name="Dr. I/C",
            vc_title="Signature of I/C"
        )
        
        ReportTest.objects.create(
            report=self.report,
            test_name="Dengue IgM",
            result_value="12.0",
            test_method="ELISA",
            interpretation_text="Positive"
        )
        
        self.client = Client()
        self.client.login(username="rmnihr", password="rmnihr03072026")

    def test_colored_report_print(self):
        response = self.client.get(reverse('view_report', kwargs={'pk': self.report.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Prep Agent")
        self.assertContains(response, "Dr. I/C")

    def test_bw_report_print(self):
        response = self.client.get(reverse('view_report_bw', kwargs={'pk': self.report.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Prep Agent")
        self.assertContains(response, "Dr. I/C")

    def test_aiims_report_print(self):
        response = self.client.get(reverse('view_report_aiims', kwargs={'pk': self.report.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Sample Details:")
        self.assertContains(response, "Dr. I/C")


