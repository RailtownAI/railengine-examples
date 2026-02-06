"use client";

import { useState, useEffect, Suspense, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Layout,
  Typography,
  Empty,
  Button,
  Spin,
  Space,
  Table,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  AutoComplete,
  Row,
  Col,
  Card,
  message,
} from "antd";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { searchMeals, type Meal } from "@/lib/meals";
import type { FoodDiaryItem } from "@/lib/schema";
import type { ColumnsType } from "antd/es/table";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

type GroupedByMeal = {
  breakfast: FoodDiaryItem[];
  lunch: FoodDiaryItem[];
  dinner: FoodDiaryItem[];
};

function getTodayDateString(): string {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (date.getTime() === today.getTime()) {
    return "Today";
  }

  return date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function getPreviousDay(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  date.setDate(date.getDate() - 1);
  return date.toISOString().split("T")[0];
}

function getNextDay(dateString: string): string {
  const date = new Date(dateString + "T00:00:00");
  date.setDate(date.getDate() + 1);
  return date.toISOString().split("T")[0];
}

const { Option } = Select;

function HomeContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [groupedData, setGroupedData] = useState<GroupedByMeal>({
    breakfast: [],
    lunch: [],
    dinner: [],
  });
  const [fetching, setFetching] = useState(true);
  const [allDocuments, setAllDocuments] = useState<FoodDiaryItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [preselectedMeal, setPreselectedMeal] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [formLoading, setFormLoading] = useState(false);
  const [mealOptions, setMealOptions] = useState<{ value: string; meal: Meal }[]>([]);
  const [selectedMeal, setSelectedMeal] = useState<Meal | null>(null);
  const nameInputRef = useRef<any>(null);

  const selectedDate = searchParams.get("date") || getTodayDateString();

  const fetchDocuments = async () => {
    setFetching(true);
    try {
      const response = await fetch("/api/retrieve");
      if (response.ok) {
        const data: FoodDiaryItem[] = await response.json();
        setAllDocuments(data);
      } else {
        const error = await response.text();
        console.error("Error fetching documents:", error);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    // Filter documents by selected date
    // Convert stored ISO date to local date string for comparison
    const itemsForDate = allDocuments.filter((item) => {
      const itemDateObj = new Date(item.date);
      // Get local date string (YYYY-MM-DD)
      const year = itemDateObj.getFullYear();
      const month = String(itemDateObj.getMonth() + 1).padStart(2, "0");
      const day = String(itemDateObj.getDate()).padStart(2, "0");
      const itemDate = `${year}-${month}-${day}`;
      return itemDate === selectedDate;
    });

    // Group documents by meal
    const grouped: GroupedByMeal = {
      breakfast: [],
      lunch: [],
      dinner: [],
    };

    itemsForDate.forEach((item) => {
      const meal = item.meal.toLowerCase();
      if (meal === "breakfast" || meal === "lunch" || meal === "dinner") {
        const mealKey = meal as keyof GroupedByMeal;
        const mealArray = grouped[mealKey];
        if (mealArray) {
          mealArray.push(item);
        }
      }
    });

    setGroupedData(grouped);
  }, [allDocuments, selectedDate]);

  useEffect(() => {
    if (isModalOpen && nameInputRef.current) {
      // Small delay to ensure the modal is fully rendered
      setTimeout(() => {
        const input = nameInputRef.current?.input || nameInputRef.current;
        input?.focus();
      }, 100);
    }
  }, [isModalOpen]);

  const handlePreviousDay = () => {
    const prevDate = getPreviousDay(selectedDate);
    router.push(`/?date=${prevDate}`);
  };

  const handleNextDay = () => {
    const nextDate = getNextDay(selectedDate);
    router.push(`/?date=${nextDate}`);
  };

  const handleOpenModal = (mealType?: string) => {
    setPreselectedMeal(mealType || null);
    setIsModalOpen(true);
    if (mealType) {
      form.setFieldsValue({ meal: mealType });
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setPreselectedMeal(null);
    setSelectedMeal(null);
    setMealOptions([]);
    form.resetFields();
  };

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
    setFormLoading(true);

    // Use the selected date from the current page context
    const entryDate = selectedDate;

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
        handleCloseModal();
        // Refresh the document list
        await fetchDocuments();
      } else {
        const error = await response.text();
        message.error(`Error: ${error}`);
      }
    } catch (error) {
      message.error(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (item: FoodDiaryItem) => {
    try {
      const response = await fetch("/api/delete", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: item.id }),
      });

      if (response.ok) {
        message.success("Entry deleted successfully!");
        // Refresh the document list
        await fetchDocuments();
      } else {
        const error = await response.text();
        message.error(`Error: ${error}`);
      }
    } catch (error) {
      message.error(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  const columns: ColumnsType<FoodDiaryItem> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: (
        <div>
          <div>Calories</div>
          <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>kcal</div>
        </div>
      ),
      dataIndex: ["nutritional_info", "calories"],
      key: "calories",
      align: "right",
    },
    {
      title: (
        <div>
          <div>Carbs</div>
          <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
        </div>
      ),
      dataIndex: ["nutritional_info", "carbohydrates"],
      key: "carbs",
      align: "right",
      render: (value: number) => `${value}g`,
    },
    {
      title: (
        <div>
          <div>Protein</div>
          <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
        </div>
      ),
      dataIndex: ["nutritional_info", "protein"],
      key: "protein",
      align: "right",
      render: (value: number) => `${value}g`,
    },
    {
      title: (
        <div>
          <div>Fat</div>
          <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
        </div>
      ),
      dataIndex: ["nutritional_info", "fat"],
      key: "fat",
      align: "right",
      render: (value: number) => `${value}g`,
    },
    {
      title: (
        <div>
          <div>Sugar</div>
          <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
        </div>
      ),
      dataIndex: ["nutritional_info", "sugar"],
      key: "sugar",
      align: "right",
      render: (value: number) => `${value}g`,
    },
    {
      title: "",
      key: "actions",
      width: 80,
      render: (_: any, record: FoodDiaryItem) => (
        <Button size="small" type="link" danger onClick={() => handleDelete(record)}>
          Remove
        </Button>
      ),
    },
  ];

  const renderMealSection = (
    mealType: "breakfast" | "lunch" | "dinner",
    title: string,
  ) => {
    const items = groupedData[mealType];
    return (
      <div style={{ marginBottom: "2rem" }}>
        <Title level={3} style={{ marginBottom: "1rem", textTransform: "capitalize" }}>
          {title}
        </Title>
        {items.length === 0 ? (
          <div style={{ textAlign: "center", padding: "2rem" }}>
            <Button type="primary" onClick={() => handleOpenModal(mealType)}>
              Add Entry
            </Button>
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={items}
            rowKey="id"
            pagination={false}
            size="small"
          />
        )}
      </div>
    );
  };

  const renderTotalsSection = () => {
    // Calculate totals across all meals
    const allItems = [
      ...groupedData.breakfast,
      ...groupedData.lunch,
      ...groupedData.dinner,
    ];

    const totals = allItems.reduce(
      (acc, item) => ({
        calories: acc.calories + item.nutritional_info.calories,
        carbs: acc.carbs + item.nutritional_info.carbohydrates,
        protein: acc.protein + item.nutritional_info.protein,
        fat: acc.fat + item.nutritional_info.fat,
        sugar: acc.sugar + item.nutritional_info.sugar,
      }),
      { calories: 0, carbs: 0, protein: 0, fat: 0, sugar: 0 },
    );

    // Daily goals (you can customize these)
    const dailyGoals = {
      calories: 2500,
      carbs: 125,
      protein: 250,
      fat: 111,
      sugar: 38,
    };

    const remaining = {
      calories: dailyGoals.calories - totals.calories,
      carbs: dailyGoals.carbs - totals.carbs,
      protein: dailyGoals.protein - totals.protein,
      fat: dailyGoals.fat - totals.fat,
      sugar: dailyGoals.sugar - totals.sugar,
    };

    const summaryColumns: ColumnsType<{
      label: string;
      calories: number;
      carbs: number;
      protein: number;
      fat: number;
      sugar: number;
    }> = [
      {
        title: "",
        dataIndex: "label",
        key: "label",
        width: 150,
      },
      {
        title: (
          <div>
            <div>Calories</div>
            <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>kcal</div>
          </div>
        ),
        dataIndex: "calories",
        key: "calories",
        align: "right",
        render: (value: number) => value.toLocaleString(),
      },
      {
        title: (
          <div>
            <div>Carbs</div>
            <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
          </div>
        ),
        dataIndex: "carbs",
        key: "carbs",
        align: "right",
        render: (value: number) => `${value}g`,
      },
      {
        title: (
          <div>
            <div>Protein</div>
            <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
          </div>
        ),
        dataIndex: "protein",
        key: "protein",
        align: "right",
        render: (value: number) => `${value}g`,
      },
      {
        title: (
          <div>
            <div>Fat</div>
            <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
          </div>
        ),
        dataIndex: "fat",
        key: "fat",
        align: "right",
        render: (value: number) => `${value}g`,
      },
      {
        title: (
          <div>
            <div>Sugar</div>
            <div style={{ fontSize: "0.75em", fontWeight: "normal" }}>g</div>
          </div>
        ),
        dataIndex: "sugar",
        key: "sugar",
        align: "right",
        render: (value: number) => `${value}g`,
      },
    ];

    const summaryData = [
      {
        key: "totals",
        label: "Totals",
        calories: totals.calories,
        carbs: totals.carbs,
        protein: totals.protein,
        fat: totals.fat,
        sugar: totals.sugar,
      },
      {
        key: "goals",
        label: "Your Daily Goal",
        calories: dailyGoals.calories,
        carbs: dailyGoals.carbs,
        protein: dailyGoals.protein,
        fat: dailyGoals.fat,
        sugar: dailyGoals.sugar,
      },
      {
        key: "remaining",
        label: "Remaining",
        calories: remaining.calories,
        carbs: remaining.carbs,
        protein: remaining.protein,
        fat: remaining.fat,
        sugar: remaining.sugar,
      },
    ];

    return (
      <div style={{ marginTop: "3rem", marginBottom: "2rem" }}>
        <Table
          columns={summaryColumns}
          dataSource={summaryData}
          rowKey="key"
          pagination={false}
          size="small"
          rowClassName={(record: any) => {
            if (record.key === "remaining") {
              return "remaining-row";
            }
            return "";
          }}
          components={{
            body: {
              row: (props: any) => {
                const isRemaining = props["data-row-key"] === "remaining";
                return (
                  <tr
                    {...props}
                    style={
                      isRemaining
                        ? {
                            color: "#52c41a",
                            fontWeight: 500,
                          }
                        : undefined
                    }
                  />
                );
              },
            },
          }}
        />
      </div>
    );
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "#fff",
          padding: "0 24px",
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          Railengine Food Diary
        </Title>
        <Space size="large" align="center">
          <Space size="middle">
            <Button
              icon={<ChevronLeft size={16} />}
              onClick={handlePreviousDay}
              aria-label="Previous day"
            />
            <Text
              strong
              style={{ minWidth: "150px", textAlign: "center", display: "inline-block" }}
            >
              {formatDate(selectedDate)}
            </Text>
            <Button
              icon={<ChevronRight size={16} />}
              onClick={handleNextDay}
              aria-label="Next day"
            />
          </Space>
          <Button type="primary" onClick={() => handleOpenModal()}>
            Add New Entry
          </Button>
        </Space>
      </Header>
      <Content
        style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto", width: "100%" }}
      >
        {fetching ? (
          <div style={{ textAlign: "center", padding: "4rem" }}>
            <Spin size="large" />
          </div>
        ) : (
          <>
            {renderMealSection("breakfast", "Breakfast")}
            {renderMealSection("lunch", "Lunch")}
            {renderMealSection("dinner", "Dinner")}
            {renderTotalsSection()}
          </>
        )}

        <Modal
          title="Add New Entry"
          open={isModalOpen}
          onCancel={handleCloseModal}
          footer={null}
          width={selectedMeal ? 1000 : 600}
        >
          <Form form={form} layout="vertical" onFinish={handleIngest} autoComplete="off">
            <Row gutter={24}>
              <Col xs={24} lg={selectedMeal ? 14 : 24}>
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

                <Form.Item
                  label="Name"
                  name="name"
                  rules={[
                    { required: true, message: "Please select or enter a food name!" },
                  ]}
                >
                  <AutoComplete
                    ref={nameInputRef}
                    placeholder="Search for a meal..."
                    options={mealOptions}
                    onSearch={handleNameSearch}
                    onSelect={handleNameSelect}
                    onChange={handleNameChange}
                    filterOption={false}
                    style={{ width: "100%" }}
                    autoFocus
                  />
                </Form.Item>

                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={formLoading} block>
                    Add Entry
                  </Button>
                </Form.Item>
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
        </Modal>
      </Content>
    </Layout>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <Layout style={{ minHeight: "100vh" }}>
          <Content style={{ padding: "24px", textAlign: "center" }}>
            <Spin size="large" />
          </Content>
        </Layout>
      }
    >
      <HomeContent />
    </Suspense>
  );
}
