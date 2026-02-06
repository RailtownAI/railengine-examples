"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Layout,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Card,
  Typography,
  message,
  AutoComplete,
  Row,
  Col,
} from "antd";
import Link from "next/link";
import { searchMeals, type Meal } from "@/lib/meals";

const { Header, Content } = Layout;
const { Title } = Typography;
const { Option } = Select;

function getTodayDateString(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function AddPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [mealOptions, setMealOptions] = useState<{ value: string; meal: Meal }[]>([]);
  const [selectedMeal, setSelectedMeal] = useState<Meal | null>(null);

  useEffect(() => {
    const mealParam = searchParams.get("meal");
    if (mealParam) {
      form.setFieldsValue({ meal: mealParam });
    }
  }, [searchParams, form]);

  const handleNameSearch = (value: string) => {
    const results = searchMeals(value);
    setMealOptions(
      results.map((meal) => ({
        value: meal.name,
        meal: meal,
      })),
    );
  };

  const handleNameSelect = (value: string, option: { value: string; meal: Meal }) => {
    const meal = option.meal;
    setSelectedMeal(meal);
    form.setFieldsValue({
      name: meal.name,
      calories: meal.calories,
      carbohydrates: meal.carbohydrates,
      sugar: meal.sugar,
      fat: meal.fat,
      protein: meal.protein,
    });
  };

  const handleNameChange = (value: string) => {
    if (!value) {
      setSelectedMeal(null);
      form.setFieldsValue({
        calories: undefined,
        carbohydrates: undefined,
        sugar: undefined,
        fat: undefined,
        protein: undefined,
      });
    }
  };

  const handleIngest = async (values: any) => {
    setLoading(true);

    // Get the selected date from query string, or use today's local date
    const dateParam = searchParams.get("date");
    const entryDate = dateParam || getTodayDateString();

    // Create ISO string at midnight local time for the selected date
    const localDate = new Date(entryDate + "T00:00:00");
    const dateISOString = localDate.toISOString();

    const data = {
      name: values.name,
      meal: values.meal,
      date: dateISOString,
      nutritional_info: {
        calories: values.calories,
        carbohydrates: values.carbohydrates,
        sugar: values.sugar,
        fat: values.fat,
        protein: values.protein,
      },
    };

    try {
      const response = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        message.success("Data ingested successfully!");
        form.resetFields();
        setSelectedMeal(null);
        setMealOptions([]);
        // Redirect to home page after a short delay
        setTimeout(() => {
          router.push("/");
        }, 1500);
      } else {
        const error = await response.text();
        message.error(`Error: ${error}`);
      }
    } catch (error) {
      message.error(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          display: "flex",
          alignItems: "center",
          background: "#fff",
          padding: "0 24px",
        }}
      >
        <Link href="/" style={{ marginRight: "16px" }}>
          ← Back to Food Diary
        </Link>
        <Title level={2} style={{ margin: 0 }}>
          Add New Entry
        </Title>
      </Header>
      <Content
        style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto", width: "100%" }}
      >
        <Form form={form} layout="vertical" onFinish={handleIngest} autoComplete="off">
          <Row gutter={24}>
            <Col xs={24} lg={selectedMeal ? 14 : 24}>
              <Card>
                <Form.Item
                  label="Name"
                  name="name"
                  rules={[
                    { required: true, message: "Please select or enter a food name!" },
                  ]}
                >
                  <AutoComplete
                    placeholder="Search for a meal..."
                    options={mealOptions}
                    onSearch={handleNameSearch}
                    onSelect={handleNameSelect}
                    onChange={handleNameChange}
                    filterOption={false}
                    style={{ width: "100%" }}
                  />
                </Form.Item>

                <Form.Item
                  label="Meal"
                  name="meal"
                  rules={[{ required: true, message: "Please select a meal!" }]}
                >
                  <Select placeholder="Select meal type">
                    <Option value="breakfast">Breakfast</Option>
                    <Option value="lunch">Lunch</Option>
                    <Option value="dinner">Dinner</Option>
                  </Select>
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading} block>
                    Add Entry
                  </Button>
                </Form.Item>
              </Card>
            </Col>

            {selectedMeal && (
              <Col xs={24} lg={10}>
                <Card title="Nutritional Information" style={{ background: "#fafafa" }}>
                  <Form.Item
                    label="Calories"
                    name="calories"
                    rules={[{ required: true, message: "Please input calories!" }]}
                  >
                    <InputNumber
                      style={{ width: "100%" }}
                      placeholder="Enter calories"
                      min={0}
                    />
                  </Form.Item>

                  <Form.Item
                    label="Carbohydrates (g)"
                    name="carbohydrates"
                    rules={[{ required: true, message: "Please input carbohydrates!" }]}
                  >
                    <InputNumber
                      style={{ width: "100%" }}
                      placeholder="Enter carbohydrates"
                      min={0}
                    />
                  </Form.Item>

                  <Form.Item
                    label="Sugar (g)"
                    name="sugar"
                    rules={[{ required: true, message: "Please input sugar!" }]}
                  >
                    <InputNumber
                      style={{ width: "100%" }}
                      placeholder="Enter sugar"
                      min={0}
                    />
                  </Form.Item>

                  <Form.Item
                    label="Fat (g)"
                    name="fat"
                    rules={[{ required: true, message: "Please input fat!" }]}
                  >
                    <InputNumber
                      style={{ width: "100%" }}
                      placeholder="Enter fat"
                      min={0}
                    />
                  </Form.Item>

                  <Form.Item
                    label="Protein (g)"
                    name="protein"
                    rules={[{ required: true, message: "Please input protein!" }]}
                  >
                    <InputNumber
                      style={{ width: "100%" }}
                      placeholder="Enter protein"
                      min={0}
                    />
                  </Form.Item>
                </Card>
              </Col>
            )}
          </Row>
        </Form>
      </Content>
    </Layout>
  );
}

export default function AddPage() {
  return (
    <Suspense
      fallback={
        <Layout style={{ minHeight: "100vh" }}>
          <Content style={{ padding: "24px", textAlign: "center" }}>
            <Typography.Text>Loading...</Typography.Text>
          </Content>
        </Layout>
      }
    >
      <AddPageContent />
    </Suspense>
  );
}
