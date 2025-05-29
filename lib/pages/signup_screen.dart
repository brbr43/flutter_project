import 'package:campoundnew/auth/AuthCubit.dart';
import 'package:campoundnew/pages/login_screen.dart';
import 'package:campoundnew/widget/custom_textfield.dart';
import 'package:campoundnew/widget/login_widgate.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});

  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  String? email;
  String? password;
  int? apartmentNumber;
  String? phoneNumber;
  String? selectedCity;

  List<String> cities = [
    'Zahara property ',
    'Khamre 1',
    'Khamre 2',
    'Hilltop',
    'Asokoro 5',
    'Sonuma 5',
  ];

  late final TextEditingController _phoneController;
  late final TextEditingController _emailController;
  late final TextEditingController _apartmentController;
  late final TextEditingController _complexController;
  late final TextEditingController _passwordController;

  GlobalKey<FormState> formKey = GlobalKey();
  bool loadingState = false;

  @override
  void initState() {
    super.initState();
    _phoneController = TextEditingController();
    _emailController = TextEditingController();
    _apartmentController = TextEditingController();
    _complexController = TextEditingController();
    _passwordController = TextEditingController();
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _emailController.dispose();
    _apartmentController.dispose();
    _complexController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color.fromARGB(255, 47, 7, 226),
      body: Form(
        key: formKey,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            const SizedBox(height: 75),
            CircleAvatar(
              radius: 70,
              backgroundColor: Colors.white,
              child: CircleAvatar(
                radius: 60,
                backgroundImage: AssetImage('assets/images/camp.jpg'),
              ),
            ),
            const Center(
              child: Text(
                'Welcome to our compound',
                style: TextStyle(
                    color: Colors.white, fontSize: 26, fontFamily: 'Pacifico'),
              ),
            ),
            const SizedBox(height: 75),
            const Text(
              'Register',
              style: TextStyle(color: Colors.white, fontSize: 20),
            ),
            const SizedBox(height: 20),

            // اختيار المدينة
            DropdownButtonFormField<String>(
              value: selectedCity,
              decoration: InputDecoration(
                labelText: 'Select Campound name',
                labelStyle: const TextStyle(color: Colors.white),
                enabledBorder: const OutlineInputBorder(
                  borderSide: BorderSide(color: Colors.white),
                ),
                focusedBorder: const OutlineInputBorder(
                  borderSide: BorderSide(color: Colors.white),
                ),
              ),
              items: cities.map((city) {
                return DropdownMenuItem<String>(
                  value: city,
                  child: Text(
                    city,
                    style: const TextStyle(color: Colors.black),
                  ),
                );
              }).toList(),
              onChanged: (value) {
                setState(() {
                  selectedCity = value;
                });
              },
              validator: (value) {
                if (value == null) {
                  return 'Please select a city';
                }
                return null;
              },
            ),
            const SizedBox(height: 20),

            // إدخال رقم الشقة
            LoiginWidgate(
              controller: _apartmentController,
              onChanged: (data) {
                apartmentNumber = int.tryParse(data);
              },
              text1: 'Apartment Number',
            ),
            const SizedBox(height: 16),

            // إدخال البريد الإلكتروني
            LoiginWidgate(
              controller: _emailController,
              onChanged: (data) {
                email = data;
              },
              text1: 'Email',
            ),
            const SizedBox(height: 16),

            // إدخال رقم الهاتف
            LoiginWidgate(
              controller: _phoneController,
              onChanged: (data) {
                phoneNumber = data;
              },
              text1: 'Phone Number',
            ),
            const SizedBox(height: 16),

            // إدخال كلمة المرور
            LoiginWidgate(
              controller: _passwordController,
              obscur: true,
              onChanged: (data) {
                password = data;
              },
              text1: 'Password',
            ),

            const SizedBox(height: 16),

            // زر التسجيل
            CustomTextfield(
              onTab: () {
                if (formKey.currentState!.validate()) {
                  setState(() {
                    loadingState = true;
                  });

                  // تحقق من صحة المدخلات
                  if (apartmentNumber == null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("يرجى إدخال رقم شقة صحيح")),
                    );
                    setState(() {
                      loadingState = false;
                    });
                    return;
                  }

                  if (selectedCity == null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text("يرجى اختيار المدينة")),
                    );
                    setState(() {
                      loadingState = false;
                    });
                    return;
                  }

                  // إرسال البيانات إلى الـ Cubit (نموذج التسجيل)
                  context.read<AuthCubit>().register(
                        phoneNumber!,
                        email!,
                        apartmentNumber!,
                        selectedCity!,
                        password!,
                      );

                  setState(() {
                    loadingState = false;
                  });

                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Registration successful!'),
                      backgroundColor: Colors.green,
                    ),
                  );
                }
              },
              text2: 'Sign Up',
              onChanged: (data) {},
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'Do you have an account?',
                  style: TextStyle(color: Colors.white),
                ),
                GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            LoginScreen(), // الانتقال إلى صفحة تسجيل الدخول
                      ),
                    );
                  },
                  child: const Text(
                    ' Login',
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
