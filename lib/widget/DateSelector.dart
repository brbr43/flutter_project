import 'package:flutter/material.dart';

class DateSelector extends StatelessWidget {
  final String label;
  final IconData icon;
  final double spacing;
  final DateTime? selectedDate;
  final Function(DateTime) onDateSelected;

  const DateSelector({
    Key? key,
    required this.label,
    required this.icon,
    required this.spacing,
    required this.selectedDate,
    required this.onDateSelected,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const SizedBox(width: 15),
        Text(
          label,
          style: const TextStyle(fontSize: 20),
        ),
        SizedBox(width: spacing),
        Expanded(
          child: GestureDetector(
            onTap: () => _selectDate(context),
            child: Container(
              padding: const EdgeInsets.symmetric(
                  vertical: 12, horizontal: 12), // تصغير الحواف
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(30.0), // تعديل زاوية الحدود
                border: Border.all(color: Colors.black),
              ),
              child: Row(
                mainAxisAlignment:
                    MainAxisAlignment.spaceBetween, // توزيع المحتوى بشكل جيد
                children: [
                  Text(
                    selectedDate == null
                        ? 'Select Date'
                        : '${selectedDate!.day}/${selectedDate!.month}/${selectedDate!.year}',
                    style: const TextStyle(fontSize: 14), // تصغير حجم النص
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 15),
        Icon(
          Icons.date_range,
          size: 50,
        ), // الأيقونة هنا
      ],
    );
  }

  // دالة لاختيار التاريخ من تقويم
  Future<void> _selectDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate:
          selectedDate ?? DateTime.now(), // التاريخ الحالي كقيمة افتراضية
      firstDate: DateTime(2025), // أول تاريخ يمكن اختياره
      lastDate: DateTime(2050), // آخر تاريخ يمكن اختياره
    );
    if (picked != null) {
      onDateSelected(picked); // يتم إرجاع التاريخ المحدد إلى الصفحة الرئيسية
    }
  }
}
