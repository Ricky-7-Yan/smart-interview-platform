import React, { useState } from 'react'
import './PositionSelector.css'

// Boss直聘常见岗位分类（多级树结构）
const POSITION_CATEGORIES = {
  '技术': {
    '后端开发': ['Java开发工程师', 'Python开发工程师', 'Go开发工程师', 'C++开发工程师', 'PHP开发工程师', 'Node.js开发工程师'],
    '前端开发': ['前端开发工程师', 'Vue.js开发工程师', 'React开发工程师', 'Angular开发工程师', '小程序开发工程师'],
    '移动开发': ['Android开发工程师', 'iOS开发工程师', 'Flutter开发工程师', 'React Native开发工程师'],
    '算法': ['算法工程师', '机器学习工程师', '深度学习工程师', '自然语言处理工程师', '计算机视觉工程师', '数据挖掘工程师'],
    '测试': ['测试工程师', '自动化测试工程师', '性能测试工程师', '测试开发工程师'],
    '运维': ['运维工程师', 'DevOps工程师', 'SRE工程师', '系统架构师'],
    '安全': ['网络安全工程师', '信息安全工程师', '渗透测试工程师']
  },
  '产品': {
    '产品经理': ['产品经理', '高级产品经理', '产品总监', 'B端产品经理', 'C端产品经理', '移动端产品经理'],
    '产品设计': ['UI设计师', 'UX设计师', '交互设计师', '视觉设计师', '产品设计师']
  },
  '设计': {
    '设计': ['UI设计师', 'UX设计师', '交互设计师', '视觉设计师', '平面设计师', '品牌设计师']
  },
  '运营': {
    '运营': ['运营专员', '运营经理', '用户运营', '内容运营', '活动运营', '产品运营', '电商运营', '新媒体运营', '社群运营'],
    '市场': ['市场专员', '市场经理', '品牌营销', '市场推广', 'PR专员']
  },
  '数据': {
    '数据分析': ['数据分析师', '商业分析师', '数据产品经理', '数据科学家'],
    '数据开发': ['数据开发工程师', '大数据开发工程师', 'ETL工程师']
  },
  '其他': {
    '其他': ['项目经理', '商务拓展', '销售', 'HR', '财务', '法务']
  }
}

function PositionSelector({ selectedPositions = [], onChange, maxSelections = 10, singleSelect = false }) {
  const [expandedCategories, setExpandedCategories] = useState({})
  const [expandedSubcategories, setExpandedSubcategories] = useState({})

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  const toggleSubcategory = (category, subcategory) => {
    const key = `${category}-${subcategory}`
    setExpandedSubcategories(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const handlePositionClick = (position) => {
    if (singleSelect) {
      onChange([position])
      return
    }

    if (selectedPositions.includes(position)) {
      // 取消选择
      onChange(selectedPositions.filter(p => p !== position))
    } else {
      // 添加选择
      if (selectedPositions.length >= maxSelections) {
        alert(`最多只能选择${maxSelections}个岗位`)
        return
      }
      onChange([...selectedPositions, position])
    }
  }

  const removePosition = (position) => {
    onChange(selectedPositions.filter(p => p !== position))
  }

  return (
    <div className="position-selector">
      {selectedPositions.length > 0 && (
        <div className="selected-positions">
          <h4>已选岗位 ({selectedPositions.length}{singleSelect ? '' : `/${maxSelections}`})</h4>
          <div className="selected-tags">
            {selectedPositions.map(pos => (
              <span key={pos} className="position-tag">
                {pos}
                {!singleSelect && (
                  <button
                    className="remove-tag"
                    onClick={() => removePosition(pos)}
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="position-tree">
        {Object.entries(POSITION_CATEGORIES).map(([category, subcategories]) => (
          <div key={category} className="position-category">
            <div
              className="category-header"
              onClick={() => toggleCategory(category)}
            >
              <span className="expand-icon">
                {expandedCategories[category] ? '▼' : '▶'}
              </span>
              <span className="category-name">{category}</span>
            </div>

            {expandedCategories[category] && (
              <div className="subcategories">
                {Object.entries(subcategories).map(([subcategory, positions]) => (
                  <div key={subcategory} className="position-subcategory">
                    <div
                      className="subcategory-header"
                      onClick={() => toggleSubcategory(category, subcategory)}
                    >
                      <span className="expand-icon">
                        {expandedSubcategories[`${category}-${subcategory}`] ? '▼' : '▶'}
                      </span>
                      <span className="subcategory-name">{subcategory}</span>
                    </div>

                    {expandedSubcategories[`${category}-${subcategory}`] && (
                      <div className="positions-list">
                        {positions.map(position => (
                          <div
                            key={position}
                            className={`position-item ${selectedPositions.includes(position) ? 'selected' : ''}`}
                            onClick={() => handlePositionClick(position)}
                          >
                            <span className="checkbox">
                              {selectedPositions.includes(position) ? '✓' : ''}
                            </span>
                            <span>{position}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default PositionSelector