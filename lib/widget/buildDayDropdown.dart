import 'package:flutter/material.dart';

class buildDayDropdown extends StatelessWidget {
  final String label;
  final IconData icon;
  final double spacing;

  const buildDayDropdown({
    Key? key,
    required this.label,
    required this.icon,
    required this.spacing,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    List<String> days = [
      'Saturday',
      'Sunday',
      'Monday',
      'Tuesday',
      'Wednesday',
      'Thursday',
      'Friday'
    ];

    return Row(
      children: [
        const SizedBox(width: 15),
        Text(
          label,
          style: const TextStyle(fontSize: 20),
        ),
        SizedBox(width: spacing),
        Expanded(
          child: DropdownButtonFormField<String>(
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30.0),
                borderSide: const BorderSide(color: Colors.black),
              ),
            ),
            items: days.map((day) {
              return DropdownMenuItem(
                value: day,
                child: Text(day),
              );
            }).toList(),
            onChanged: (value) {},
          ),
        ),
        const SizedBox(width: 15),
        Padding(
          padding: const EdgeInsets.only(right: 10),
          child: Icon(
            icon,
            size: 50,
            color: Colors.black,
          ),
        ),
      ],
    );
  }
}
